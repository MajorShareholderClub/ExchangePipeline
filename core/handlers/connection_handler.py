from adapters.base.event.enhanced_event_bus import EnhancedEventBus
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
from dataclasses import dataclass, field
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
    event_bus: EnhancedEventBus

    async def connection_publish(self, exchange_name: str, request_type: str) -> None:
        await self.event_bus.publish(
            EventType.CONNECTION_SUCCESS,
            ConnectionSuccessPayload(exchange=exchange_name, request_type=request_type),
            EventMetadata(source=f"{exchange_name}_{request_type}_connection_handler"),
            retry_on_failure=True,
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
            retry_on_failure=True,
        )


@dataclass
class ConnectionContext:
    """연결 시도에 필요한 모든 컨텍스트 정보를 포함하는 데이터 클래스"""

    sinstance: WorldWebSocket
    event_publisher: EventPublisher
    exchange_name: str
    exchange_info: dict
    parameter_info: dict
    request_type: str
    region: str


# fmt: off
@dataclass
class ConnectionHandlerRegistrar:
    event_bus: EnhancedEventBus
    retry_service: ConnectionRetryService
    _initialized: bool = field(default=False, init=False)
    
    def __post_init__(self) -> None:
        """동기적 초기화 작업"""
        self.connection_handler = ConnectionRequestHandler(self.event_bus)
        
    async def initialize(self) -> None:
        """비동기 초기화 작업"""
        if self._initialized:
            return
            
        # 이미 초기화된 retry_service를 사용합니다.
        self._initialized = True
        await connection_logger.ainfo("ConnectionHandlerRegistrar 초기화 완료")

    # 각 이벤트 타입에 대한 핸들러 등록
    async def request_wrapper(self, data: ConnectionRequestPayload) -> None:
        """연결 요청 이벤트 핸들러
        Args:
            data: ConnectionRequestPayload
        """
        await self.connection_handler.handle_request(data)

    async def close_wrapper(self, data: ConnectionClosePayload) -> None:
        """연결 종료 이벤트 핸들러
        Args:
            data: ConnectionClosePayload
        """
        await handle_connection_close(self.event_bus, data)

    async def data_wrapper(self, data: DataPayload) -> None:
        """마켓 티커 이벤트 핸들러
        Args:
            data: DataPayload
        """
        await handle_data(data)

    async def register_handlers(self) -> None:
        """연결 관련 이벤트 핸들러 등록"""
        await connection_logger.ainfo("연결 관련 이벤트 핸들러 등록 시작")

        # 초기화 확인
        if not self._initialized:
            await self.initialize()

        # 이벤트 핸들러 등록
        await self.event_bus.subscribe(EventType.CONNECTION_REQUEST, self.request_wrapper)
        await self.event_bus.subscribe(EventType.CONNECTION_CLOSE, self.close_wrapper)
        await self.event_bus.subscribe(EventType.MARKET_TICKER, self.data_wrapper)
        await self.event_bus.subscribe(EventType.MARKET_ORDERBOOK, self.data_wrapper)

        await connection_logger.ainfo("연결 관련 이벤트 핸들러 등록 완료")




async def handle_data(data: DataPayload) -> None:
    print(data)
    region: str = data.get("region", "unknown")
    exchange: str = data.get("exchange", "unknown")
    request_type: str = data.get("request_type", "unknown")
    ticker_data: dict = data.get("data", {})


    # 로깅 컨텍스트 설정
    connection_logger.set_context(exchange=exchange, request_type=request_type, region=region)
    
    if not ticker_data:
        await connection_logger.awarning("수신된 티커 데이터가 비어있습니다.")
        return
    
    symbol: str = list(ticker_data.keys())[0]
    key: str = f"{exchange}:{request_type}:{symbol}"
    topic: str = f"{region}_{request_type}"
    t_data[key].append(json.dumps(ticker_data))
    elapsed: float = time.time() - last_flush_time[key]

    await connection_logger.adebug(f"데이터 수신: key={key}, 건수: {len(t_data[key])}, 경과시간={elapsed:.2f}초")
    
    # 배치 크기 도달 또는 일정 시간 경과 시 Kafka로 전송
    if len(t_data[key]) >= BATCH_SIZE or elapsed >= BATCH_INTERVAL:
        # 데이터 복사만 하고 아직 비우지 않음
        batch: list[str] = t_data[key].copy()
        current_time: float = time.time()
        
        message: dict = {
            "exchange": exchange, 
            "time": current_time, 
            "data": batch
        }
        
        # # Kafka로 메시지 전송
        # await sender.produce_sending(message=message, topic=topic, key=key)
        
        # 전송 성공 후 데이터 비우기 및 시간 초기화
        t_data[key].clear()
        last_flush_time[key] = time.time()
        await connection_logger.ainfo(f"데이터 전송 완료: key={key}, 건수: {len(batch)}, 새로운 마지막 전송시간={last_flush_time[key]}")




@dataclass
class ConnectionRequestHandler:
    event_bus: EnhancedEventBus
    
    async def handle_request(self, data: ConnectionRequestPayload) -> None:
        print(data)
        exchange_name: str = data.get("exchange_name")
        parameter_info: dict[str, any] = data.get("parameter_info")
        request_type: str = data.get("request_type")
        region: str = data.get("region")
        sinstance: WorldWebSocket = data.get("socket_instance")(
            self.event_bus,
            exchange_name,
            region,
            request_type,
        )
        event_publisher = EventPublisher(event_bus=self.event_bus)
        exchange_info = get_exchange(exchange_name, request_type)
        
        # 컨텍스트 객체 생성
        context = ConnectionContext(
            sinstance=sinstance,
            event_publisher=event_publisher,
            exchange_name=exchange_name,
            exchange_info=exchange_info,
            parameter_info=parameter_info,
            request_type=request_type,
            region=region
        )

        # 컨텍스트 객체 하나만 전달
        await self.attempt_connection(context)

    async def attempt_connection(self, context: ConnectionContext) -> bool:
        """단일 컨텍스트 객체를 사용하여 연결 시도"""
        try:
            # 연결 및 구독 시도
            connection = await context.sinstance.connect_and_subscribe(
                config=context.parameter_info
            )

            if connection:
                # 연결 성공 이벤트 발행
                await context.event_publisher.connection_publish(
                    exchange_name=context.exchange_name,
                    request_type=context.exchange_info["request_type"],
                )
                
        except AsyncException as e:
            # 예외 처리 로직...
            await context.event_publisher.connection_failure_publish(
                exchange_name=context.exchange_name,
                error=str(e),
                retry_count=1,
                request_type=context.request_type
            )


# fmt: on
async def handle_connection_close(
    event_bus: EnhancedEventBus, data: ConnectionClosePayload
) -> None:
    """연결 종료 이벤트 핸들러

    Args:
        event_bus: 이벤트 버스 인스턴스
        data: ConnectionClosePayload
    """
    exchange_name: str = data.get("exchange_name")
    reason: str = data.get("reason")
    request_type: str = data.get("request_type")
    region: str = data.get("region", "unknown")

    # 로깅 컨텍스트 설정
    connection_logger.set_context(
        exchange=exchange_name, request_type=request_type, region=region
    )
    await connection_logger.ainfo(f"거래소 연결 종료: {exchange_name}, 이유: {reason}")

    event_publisher = EventPublisher(event_bus=event_bus)

    # 정상 종료 사유 목록
    normal_close_reasons = [
        "user_request",
        "normal_close",
        "shutdown",
        "planned_maintenance",
    ]

    # 비정상적인 종료인 경우 재연결 시도 이벤트 발행
    if reason not in normal_close_reasons:
        await connection_logger.awarning(
            f"비정상 연결 종료 발생. 재연결 시도 예정: 거래소={exchange_name}, 이유={reason}"
        )
        await event_publisher.connection_failure_publish(
            exchange_name=exchange_name,
            error=reason,
            retry_count=MAX_RETRY_COUNT,
            request_type=request_type,
        )
    else:
        await connection_logger.ainfo(
            f"정상 연결 종료: 거래소={exchange_name}, 이유={reason}"
        )
