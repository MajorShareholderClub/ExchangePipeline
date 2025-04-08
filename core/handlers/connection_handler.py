from typing import Any

from adapters.base.event.event_bus import EventBus
from adapters.base.event.types import EventType, AsyncException
from adapters.base.event.types.event_types import (
    ConnectionRequestPayload,
    ConnectionSuccessPayload,
    ConnectionFailurePayload,
    ConnectionClosePayload,
    EventMetadata,
)
from common.logger import PipelineLogger
from common.registry import get_exchange
from core.connection.retry import ConnectionRetryService


# 파이프라인 로거 설정
connection_logger = PipelineLogger.get_logger("connection", "handler")


async def register_connection_handlers(event_bus: EventBus) -> None:
    """연결 관련 이벤트 핸들러 등록

    Args:
        event_bus: 이벤트 버스 인스턴스

    Returns:
        None
    """
    connection_logger.info("연결 관련 이벤트 핸들러 등록 시작")

    # 연결 재시도 서비스 초기화
    retry_service = ConnectionRetryService(
        event_bus=event_bus, max_retries=3, retry_delay=5
    )

    # 각 이벤트 타입에 대한 핸들러 등록
    async def request_wrapper(data: Any) -> None:
        await handle_connection_request(event_bus, data)

    async def success_wrapper(data: Any) -> None:
        await handle_connection_success(event_bus, data)

    async def close_wrapper(data: Any) -> None:
        await handle_connection_close(event_bus, data)

    async def max_retry_wrapper(data: Any) -> None:
        await handle_connection_max_retry(event_bus, data)

    # 이벤트 핸들러 등록
    await event_bus.subscribe(EventType.CONNECTION_REQUEST, request_wrapper)
    await event_bus.subscribe(EventType.CONNECTION_SUCCESS, success_wrapper)
    await event_bus.subscribe(EventType.CONNECTION_CLOSE, close_wrapper)
    await event_bus.subscribe(EventType.CONNECTION_MAX_RETRY, max_retry_wrapper)

    connection_logger.info("연결 관련 이벤트 핸들러 등록 완료")


async def handle_connection_request(
    event_bus: EventBus, data: ConnectionRequestPayload
) -> None:
    """연결 요청 이벤트 핸들러

    Args:
        event_bus: 이벤트 버스 인스턴스
        data: 연결 요청 페이로드

    Returns:
        None
    """
    exchange_name = data.get("exchange_name")
    parameter_info = data.get("parameter_info")
    retry_count = data.get("retry_count", 0)

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
        # WebSocket 연결 시작 (이 부분은 실제 연결 로직을 구현해야 함)
        # 여기서는 예시로 이벤트를 발행하는 것만 구현

        # 성공적인 연결 시
        # TODO: 실제 WebSocket 연결 구현
        connection_success = True

        if connection_success:
            # 연결 성공 이벤트 발행
            await event_bus.publish(
                EventType.CONNECTION_SUCCESS,
                ConnectionSuccessPayload(exchange=exchange_name),
                EventMetadata(source=f"{exchange_name}_connection_handler"),
            )
        else:
            # 연결 실패 이벤트 발행
            await event_bus.publish(
                EventType.CONNECTION_FAILURE,
                ConnectionFailurePayload(
                    exchange=exchange_name,
                    error=f"{exchange_name}Connection failed",
                    retry_count=retry_count,
                ),
                EventMetadata(source=f"{exchange_name}_connection_handler"),
            )

    except AsyncException as e:
        # 예외 발생 시 연결 실패 이벤트 발행
        connection_logger.error(f"연결 중 예외 발생: {str(e)}", exchange=exchange_name)
        await event_bus.publish(
            EventType.CONNECTION_FAILURE,
            ConnectionFailurePayload(
                exchange=exchange_name,
                error=str(e),
                retry_count=retry_count,
            ),
            EventMetadata(source=f"{exchange_name}_connection_handler"),
        )


async def handle_connection_success(
    event_bus: EventBus, data: ConnectionSuccessPayload
) -> None:
    """연결 성공 이벤트 핸들러

    Args:
        event_bus: 이벤트 버스 인스턴스
        data: 연결 성공 페이로드

    Returns:
        None
    """
    exchange = data.get("exchange")
    connection_logger.set_context(exchange=exchange)
    connection_logger.info(f"거래소 연결 성공: {exchange}")

    # 여기서 추가적인 구독 설정이나 초기화 작업을 수행할 수 있음
    # 예: 특정 심볼에 대한 구독 설정


async def handle_connection_close(
    event_bus: EventBus, data: ConnectionClosePayload
) -> None:
    """연결 종료 이벤트 핸들러

    Args:
        event_bus: 이벤트 버스 인스턴스
        data: 연결 종료 페이로드

    Returns:
        None
    """
    exchange_name = data.get("exchange_name")
    reason = data.get("reason")

    connection_logger.set_context(exchange=exchange_name)
    connection_logger.info(f"거래소 연결 종료: {exchange_name}, 이유: {reason}")

    # 비정상적인 종료인 경우 재연결 시도 이벤트 발행
    if reason not in ["user_request", "normal_close", "shutdown"]:
        await event_bus.publish(
            EventType.CONNECTION_FAILURE,
            ConnectionFailurePayload(
                exchange=exchange_name,
                error=f"Abnormal closure: {reason}",
                retry_count=0,
            ),
            EventMetadata(source=f"{exchange_name}_connection_handler"),
        )


async def handle_connection_max_retry(event_bus: EventBus, data: Any) -> None:
    """최대 재시도 횟수 초과 이벤트 핸들러

    Args:
        event_bus: 이벤트 버스 인스턴스
        data: 최대 재시도 횟수 초과 페이로드

    Returns:
        None
    """
    exchange = data.get("exchange")
    max_retries = data.get("max_retries")
    error = data.get("error")

    connection_logger.set_context(exchange=exchange)
    connection_logger.error(
        f"최대 재시도 횟수 초과 ({max_retries}회): {error}",
        exchange=exchange,
        max_retries=max_retries,
        error=error,
    )

    # 알림 또는 모니터링 시스템에 장애 보고 등의 추가 작업 수행 가능
