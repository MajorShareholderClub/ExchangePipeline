from adapters.base.event.event_bus import EventBus
from adapters.base.event.types import EventType
from adapters.base.event.types.event_types import (
    ConnectionRequestPayload,
    ConnectionSuccessPayload,
    ConnectionFailurePayload,
    ConnectionClosePayload,
    EventMetadata,
    DataPayload,
)
import json
from adapters.exchange import WorldWebSocket
from common.exceptions import AsyncException
from common.logger import PipelineLogger
from common.registry import get_exchange
from core.connection.retry import ConnectionRetryService
from dataclasses import dataclass
from collections import defaultdict
from messaging.data_interaction import KafkaMessageSender
import time


# 파이프라인 로거 설정
connection_logger = PipelineLogger.get_logger("connection", "handler")
t_data = defaultdict(list)
last_flush_time = defaultdict(lambda: time.time())
sender = KafkaMessageSender()

BATCH_SIZE = 50
BATCH_INTERVAL = 10
MAX_RETRY_COUNT = 3


@dataclass
class EventPublisher:
    event_bus: EventBus

    async def connection_publish(self, exchange_name: str, request_type: str) -> None:
        await self.event_bus.publish(
            EventType.CONNECTION_SUCCESS,
            ConnectionSuccessPayload(exchange=exchange_name, request_type=request_type),
            EventMetadata(source=f"{exchange_name}_{request_type}_connection_handler"),
        )

    async def connection_failure_publish(
        self, exchange_name: str, error: str, retry_count: int, request_type: str
    ) -> None:
        await self.event_bus.publish(
            EventType.CONNECTION_FAILURE,
            ConnectionFailurePayload(
                exchange=exchange_name,
                error=error,
                retry_count=retry_count,
                request_type=request_type,
            ),
            EventMetadata(source=f"{exchange_name}_{request_type}_connection_handler"),
        )


# fmt: off
@dataclass
class ConnectionHandlerRegistrar:
    event_bus: EventBus
    retry_service: ConnectionRetryService

    # 각 이벤트 타입에 대한 핸들러 등록
    async def request_wrapper(self, data: ConnectionRequestPayload) -> None:
        """연결 요청 이벤트 핸들러
        Args:
            data: ConnectionRequestPayload
        """
        await handle_connection_request(self.event_bus, data)

    async def close_wrapper(self, data: ConnectionClosePayload) -> None:
        """연결 종료 이벤트 핸들러
        Args:
            data: ConnectionClosePayload
        """
        await handle_connection_close(self.event_bus, data)

    async def ticker_wrapper(self, data: DataPayload) -> None:
        """마켓 티커 이벤트 핸들러
        Args:
            data: DataPayload
        """
        await handle_ticker(data)

    async def register_handlers(self) -> None:
        """연결 관련 이벤트 핸들러 등록"""
        await connection_logger.ainfo("연결 관련 이벤트 핸들러 등록 시작")

        # 이벤트 핸들러 등록
        await self.event_bus.subscribe(EventType.CONNECTION_REQUEST, self.request_wrapper)
        await self.event_bus.subscribe(EventType.CONNECTION_CLOSE, self.close_wrapper)
        await self.event_bus.subscribe(EventType.MARKET_TICKER, self.ticker_wrapper)

        await connection_logger.ainfo("연결 관련 이벤트 핸들러 등록 완료")



async def handle_ticker(data: DataPayload) -> None:    
    exchange: str = data.get("exchange", "unknown")
    response_type: str = data.get("response_type", "unknown")
    ticker_data: dict = data.get("data", {})

    symbol = list(ticker_data.keys())[0]
    key = f"{exchange}:{response_type}:{ticker_data[symbol]}"
    t_data[key].append(json.dumps(ticker_data))
    elapsed: float = time.time() - last_flush_time[key]

    if len(t_data[key]) >= BATCH_SIZE or elapsed >= BATCH_INTERVAL:
        # 데이터 복사만 하고 아직 비우지 않음
        batch = t_data[key].copy()
        current_time = time.time()
        
        message = {"exchange": exchange, "time": current_time, "data": batch}
        
        # Kafka로 메시지 전송
        await sender.produce_sending(message=message, topic="ticker", key=key)
        
        # 전송 성공 후 데이터 비우기 및 시간 초기화
        t_data[key].clear()
        last_flush_time[key] = time.time()
        print(f"[FLUSHED] key={key}, 건수: {len(batch)}, new_last_flush_time={last_flush_time[key]}")


# fmt: on
async def handle_connection_request(
    event_bus: EventBus, data: ConnectionRequestPayload
) -> None:
    """연결 요청 이벤트 핸들러

    Args:
        event_bus: 이벤트 버스 인스턴스
        data: 연결 요청 페이로드
    """
    exchange_name: str = data.get("exchange_name")
    parameter_info: dict = data.get("parameter_info")
    request_type: str = data.get("request_type")
    sinstance: WorldWebSocket = data.get("socket_instance")(event_bus, exchange_name)

    event_publisher = EventPublisher(event_bus=event_bus)

    connection_logger.set_context(exchange=exchange_name)
    await connection_logger.ainfo(
        f"거래소 연결 요청: {exchange_name}, Parameter: {parameter_info}"
    )

    # 거래소 정보 조회
    exchange_info = get_exchange(exchange_name, request_type)

    if not exchange_info:
        await connection_logger.aerror(f"지원하지 않는 거래소: {exchange_name}")
        return

    try:
        connection = await sinstance.connect_and_subscribe(config=parameter_info)

        if connection:
            # 연결 성공 이벤트 발행
            await event_publisher.connection_publish(
                exchange_name=exchange_name,
                request_type=exchange_info["request_type"],
            )

    except AsyncException as e:
        # 예외 발생 시 연결 실패 이벤트 발행
        await connection_logger.aerror(
            f"연결 중 예외 발생: {str(e)}", exchange=exchange_name
        )
        await event_publisher.connection_failure_publish(
            exchange_name=exchange_name,
            error=str(e),
            retry_count=3,
        )


# fmt: on
async def handle_connection_close(
    event_bus: EventBus, data: ConnectionClosePayload
) -> None:
    """연결 종료 이벤트 핸들러

    Args:
        event_bus: 이벤트 버스 인스턴스
        data: ConnectionClosePayload
    """
    exchange_name: str = data.get("exchange_name")
    reason: str = data.get("reason")
    request_type: str = data.get("request_type")

    connection_logger.set_context(exchange=exchange_name)
    await connection_logger.ainfo(f"거래소 연결 종료: {exchange_name}, 이유: {reason}")
    event_publisher = EventPublisher(event_bus=event_bus)

    # 비정상적인 종료인 경우 재연결 시도 이벤트 발행
    if reason not in ["user_request", "normal_close", "shutdown"]:
        await event_publisher.connection_failure_publish(
            exchange_name=exchange_name,
            error=reason,
            retry_count=3,
            request_type=request_type,
        )
