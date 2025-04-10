from adapters.base.event.event_bus import EventBus
from adapters.base.event.types import EventType, AsyncException
from adapters.base.event.types.event_types import (
    ConnectionRequestPayload,
    ConnectionSuccessPayload,
    ConnectionFailurePayload,
    ConnectionClosePayload,
    EventMetadata,
)
from adapters.exchange import WorldWebSocket
from common.logger import PipelineLogger
from common.registry import get_exchange
from core.connection.retry import ConnectionRetryService
from dataclasses import dataclass

# 파이프라인 로거 설정
connection_logger = PipelineLogger.get_logger("connection", "handler")


@dataclass
class EventPublisher:
    event_bus: EventBus

    async def connection_publish(self, exchange_name: str) -> None:
        await self.event_bus.publish(
            EventType.CONNECTION_SUCCESS,
            ConnectionSuccessPayload(exchange=exchange_name),
            EventMetadata(source=f"{exchange_name}_connection_handler"),
        )

    async def connection_failure_publish(self, exchange_name: str) -> None:
        await self.event_bus.publish(
            EventType.CONNECTION_FAILURE,
            ConnectionFailurePayload(exchange=exchange_name),
            EventMetadata(source=f"{exchange_name}_connection_handler"),
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

    async def register_handlers(self) -> None:
        """연결 관련 이벤트 핸들러 등록"""
        connection_logger.info("연결 관련 이벤트 핸들러 등록 시작")

        # 이벤트 핸들러 등록
        await self.event_bus.subscribe(EventType.CONNECTION_REQUEST, self.request_wrapper)
        await self.event_bus.subscribe(EventType.CONNECTION_CLOSE, self.close_wrapper)

        connection_logger.info("연결 관련 이벤트 핸들러 등록 완료")


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
    sinstance: WorldWebSocket = data.get("socket_instance")(event_bus, exchange_name)

    event_publisher = EventPublisher(event_bus=event_bus)

    connection_logger.set_context(exchange=exchange_name)
    connection_logger.info(
        f"거래소 연결 요청: {exchange_name}, Parameter: {parameter_info}"
    )

    # 거래소 정보 조회
    exchange_info = get_exchange(exchange_name)

    if not exchange_info:
        connection_logger.error(f"지원하지 않는 거래소: {exchange_name}")
        return

    try:
        connection = await sinstance.connect_and_subscribe(config=parameter_info)

        if connection:
            # 연결 성공 이벤트 발행
            await event_publisher.connection_publish(exchange_name=exchange_name)
        else:
            # 연결 실패 이벤트 발행
            await event_publisher.connection_failure_publish(
                exchange_name=exchange_name
            )

    except AsyncException as e:
        # 예외 발생 시 연결 실패 이벤트 발행
        connection_logger.error(f"연결 중 예외 발생: {str(e)}", exchange=exchange_name)
        await event_publisher.connection_failure_publish(exchange_name=exchange_name)


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

    connection_logger.set_context(exchange=exchange_name)
    connection_logger.info(f"거래소 연결 종료: {exchange_name}, 이유: {reason}")
    event_publisher = EventPublisher(event_bus=event_bus)

    # 비정상적인 종료인 경우 재연결 시도 이벤트 발행
    if reason not in ["user_request", "normal_close", "shutdown"]:
        await event_publisher.connection_failure_publish(exchange_name=exchange_name)
