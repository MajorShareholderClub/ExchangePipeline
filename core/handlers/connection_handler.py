import time
import json
import asyncio
from dataclasses import dataclass, field
from collections import defaultdict, deque

from adapters.exchange import WorldWebSocket
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
from common.exceptions import AsyncException
from common.setting.types import ExchangeMetadata
from common.logger import PipelineLogger
from messaging.data_interaction import KafkaMessageSender
from cachetools import TTLCache  # type: ignore


try:
    from cachetools import TTLCache  # type: ignore
except ModuleNotFoundError:
    TTLCache = None  # type: ignore

"""
connection_logger -> 로깅
t_data -> 담을 데이터 
last_flush_time -> 마지막 플러시 시간
sender -> Kafka 메시지 전송
exchange_stats -> 각 거래소별 전송 통계 추적
"""
connection_logger = PipelineLogger.get_logger("connection", "handler")
t_data: defaultdict[str, deque[dict]] = defaultdict(deque)
last_flush_time = defaultdict(lambda: time.time())
sender = KafkaMessageSender()
exchange_stats = defaultdict(
    lambda: {"count": 0, "messages": 0, "last_report": time.time()}
)

"""
# ----- 상수 설정 -----
STAT_REPORT_INTERVAL -> 통계 로그 출력 주기 (5분)
BATCH_SIZE ->  배치 사이즈
BATCH_INTERVAL -> 배치 시간 
MAX_RETRY_COUNT -> 최대 재시도 횟수

"""
STAT_REPORT_INTERVAL = 300
BATCH_SIZE = 20
BATCH_INTERVAL = 5
MAX_RETRY_COUNT = 3

# purge 관련 상수 (idle buffer → 메모리 누수 방지)
IDLE_BUFFER_LIFETIME = 300  # 초
PURGE_INTERVAL = 60  # 초


# TTLCache 초기화 (위에서 try-import)
if TTLCache:
    last_flush_time = TTLCache(maxsize=10_000, ttl=IDLE_BUFFER_LIFETIME)  # type: ignore


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

    metadata: ExchangeMetadata
    sinstance: WorldWebSocket
    event_publisher: EventPublisher
    parameter_info: dict


# fmt: off
@dataclass
class ConnectionHandlerRegistrar:
    event_bus: EnhancedEventBus
    _purge_task: asyncio.Task | None = field(default=None, init=False)
    
    def __post_init__(self) -> None:
        """동기적 초기화 작업"""
        self.connection_handler = ConnectionRequestHandler(self.event_bus)
        self.data_batch_handler = DataBatchHandler(sender=sender, connection_logger=connection_logger)

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
        await self.data_batch_handler.accumulate_data(data)

    async def register_handlers(self) -> None:
        """연결 관련 이벤트 핸들러 등록"""
        await connection_logger.ainfo("연결 관련 이벤트 핸들러 등록 시작")

        # 이벤트 핸들러 등록
        await self.event_bus.subscribe(EventType.CONNECTION_REQUEST, self.request_wrapper)
        await self.event_bus.subscribe(EventType.CONNECTION_CLOSE, self.close_wrapper)
        await self.event_bus.subscribe(EventType.MARKET_TICKER, self.data_wrapper)
        await self.event_bus.subscribe(EventType.MARKET_ORDERBOOK, self.data_wrapper)

        await connection_logger.ainfo("연결 관련 이벤트 핸들러 등록 완료")

        # 버퍼 정리 태스크 시작
        await self._start_buffer_maintenance()

    async def _start_buffer_maintenance(self) -> None:
        """버퍼 정리 백그라운드 태스크를 시작합니다."""
        if self._purge_task is None or self._purge_task.done():
            self._purge_task = asyncio.create_task(self._purge_idle_buffers())
            await connection_logger.ainfo("Idle buffer purge task started")

    async def _purge_idle_buffers(self) -> None:
        """주기적으로 전송 지연 버퍼를 정리해 메모리 사용을 제한합니다."""
        while True:
            try:
                now: float = time.time()
                # t_data 복사본으로 작업하여 순회 중 변경 방지
                keys_to_check = list(t_data.keys())
                
                for k in keys_to_check:
                    # 각 키에 대해 별도 검사하여 경쟁 조건 감소
                    if k in t_data and k in last_flush_time:
                        if now - last_flush_time[k] > IDLE_BUFFER_LIFETIME:
                            cnt: int = len(t_data[k])
                            t_data.pop(k, None)
                            last_flush_time.pop(k, None)
                            await connection_logger.awarning(
                                f"Idle buffer purged: {k} (dropped {cnt} messages)"
                            )
                
                await asyncio.sleep(PURGE_INTERVAL)
            except asyncio.CancelledError:
                # 작업 취소 시 정상 종료
                break
            except Exception as exc:  # pragma: no cover
                await connection_logger.error(f"Buffer purge task error: {exc}")
                # 오류 발생해도 계속 실행
                await asyncio.sleep(PURGE_INTERVAL)


@dataclass
class DataBatchHandler:
    sender: KafkaMessageSender
    connection_logger: PipelineLogger

    async def accumulate_data(self, data: DataPayload) -> None:
        """데이터 적재 및 플러시 여부 판단"""
        region = data.get("region", "unknown")
        exchange = data.get("exchange", "unknown")
        request_type = data.get("request_type", "unknown")
        dict_data = data.get("data", {})

        if not dict_data:
            await self.connection_logger.awarning("수신된 데이터가 비어있습니다.")
            return

        # key/topic 생성
        symbol_key: str = next(iter(dict_data))
        symbol: str = dict_data[symbol_key]
        key: str = f"{exchange}:{request_type}:{symbol}"
        topic: str = f"{region}_{request_type}"

        # 데이터 적재
        t_data[key].append(dict_data)

        # 첫 접근 시 타임스탬프 초기화
        now: float = time.time()
        last_flush_time.setdefault(key, now)
        elapsed = now - last_flush_time[key]

        # 배치 조건 검사
        if len(t_data[key]) >= BATCH_SIZE or elapsed >= BATCH_INTERVAL:
            await self._flush_batch_if_needed(key, topic, exchange)

    async def _flush_batch_if_needed(self, key: str, topic: str, exchange: str) -> None:
        """배치 전송, 클리어, 통계 업데이트 및 로깅"""
        batch = t_data[key].copy()
        if not batch:
            return

        current_time: float = time.time()
        # JSON 직렬화
        json_batch: list[str] = [json.dumps(item, default=str) for item in batch]

        # Kafka 전송
        message: dict[str, float | list[str] | str] = {
            "exchange": exchange,
            "time": current_time,
            "data": json_batch,
        }
        await self.sender.produce_sending(message=message, topic=topic, key=key)

        # 전송 후 초기화
        t_data[key].clear()
        last_flush_time[key] = current_time

        # 통계 업데이트
        stats = exchange_stats[exchange]
        stats["count"] += 1
        stats["messages"] += len(batch)

        # 주기적 통계 로깅 (5분마다)
        if current_time - stats.get("last_report", 0) >= STAT_REPORT_INTERVAL:
            stats_logger = self.connection_logger.get_logger("stats", exchange, location2="exchange")
            stats_logger.set_context(exchange=exchange)
            await stats_logger.ainfo(
                f"5분 통계: {exchange} - 배치수: {stats['count']}, 메시지수: {stats['messages']}"
            )
            # 통계 리셋
            stats["count"] = 0
            stats["messages"] = 0
            stats["last_report"] = current_time


@dataclass
class ConnectionRequestHandler:
    event_bus: EnhancedEventBus

    async def handle_request(self, data: ConnectionRequestPayload) -> None:
        metadata: ExchangeMetadata = data.get("metadata")
        parameter_info: dict[str, any] = data.get("parameter_info")
        sinstance: WorldWebSocket = data.get("socket_instance")(
            self.event_bus,
            metadata["exchange_name"],
            metadata["region"],
            metadata["request_type"],
        )
        event_publisher = EventPublisher(event_bus=self.event_bus)

        # 컨텍스트 객체 생성
        context = ConnectionContext(
            sinstance=sinstance,
            event_publisher=event_publisher,
            metadata=metadata,
            parameter_info=parameter_info,
        )

        # 컨텍스트 객체 하나만 전달
        await self.attempt_connection(context)

    async def attempt_connection(self, context: ConnectionContext) -> bool:
        """단일 컨텍스트 객체를 사용하여 연결 시도"""
        try:
            # 연결 및 구독 시도
            connection = await context.sinstance.connect_and_subscribe(
                metadata=context.metadata, parameter_info=context.parameter_info
            )
            if connection:
                # 연결 성공 이벤트 발행
                await context.event_publisher.connection_publish(
                    exchange_name=context.metadata["exchange_name"],
                    request_type=context.metadata["request_type"],
                )

        except AsyncException as e:
            # 예외 처리 로직...
            await context.event_publisher.connection_failure_publish(
                exchange_name=context.metadata["exchange_name"],
                error=str(e),
                retry_count=1,
                request_type=context.metadata["request_type"],
            )


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
