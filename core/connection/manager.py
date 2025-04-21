import asyncio

from adapters.base.event.event_bus import EventBus
from adapters.base.event.types import EventType
from adapters.base.event.types.event_types import (
    ConnectionRequestPayload,
    EventMetadata,
)
from common.exceptions import AsyncException
from common.logger import PipelineLogger
from common.registry import get_exchange, get_all_exchanges
from core.handlers.connection_handler import ConnectionHandlerRegistrar
from core.connection.retry import ConnectionRetryService

# 파이프라인 로거 설정
manager_logger = PipelineLogger.get_logger("connection", "manager")


async def setup_event_handlers(event_bus: EventBus) -> None:
    """이벤트 핸들러 등록 함수"""
    manager_logger.info("이벤트 구독 등록")

    # 새로운 연결 관련 핸들러 및 retry 서비스 등록
    retry_service = ConnectionRetryService(event_bus)
    await ConnectionHandlerRegistrar(
        event_bus,
        retry_service,
    ).register_handlers()

    manager_logger.info("이벤트 구독 완료")


async def run_all_exchanges(
    request_type: str,
    exchange_names: list[str] = None,
) -> None:
    """모든 거래소를 동시에 실행하는 함수"""
    manager_logger.info("거래소 동시 연결 시작")

    # 이벤트 버스 초기화
    event_bus = EventBus()
    manager_logger.info("이벤트 버스 초기화")
    await event_bus.start()

    try:
        # 이벤트 핸들러 등록
        await setup_event_handlers(event_bus)
        exchange: str = (
            f"{len(exchange_names)}개) 거래소 목록: {', '.join(exchange_names)}"
        )

        # 지정된 거래소가 없으면 모든 거래소 실행
        if not exchange_names:
            exchange_names = list(get_all_exchanges(request_type).keys())
            manager_logger.info(f"모든 거래소 연결 시작 {exchange}")
        else:
            manager_logger.info(f"지정된 거래소 연결 시작 {exchange}")

        # 각 거래소에 대한 연결 요청을 병렬로 처리하기 위한 함수
        async def request_connection(exchange_name: str, request_type: str) -> None:
            socket_parameter = get_exchange(exchange_name, request_type)

            if not socket_parameter:
                manager_logger.error(f"지원하지 않는 거래소: {exchange_name}")
                return

            # 연결 요청 이벤트 발행
            await event_bus.publish(
                EventType.CONNECTION_REQUEST,
                ConnectionRequestPayload(
                    region=socket_parameter["parameter_info"]["region"],
                    exchange_name=exchange_name,
                    request_type=request_type,
                    parameter_info=socket_parameter["parameter_info"],
                    socket_instance=socket_parameter["socket"],
                    retry_count=3,  # 초기값 0으로 설정
                ),
                EventMetadata(source=f"{exchange_name}_connection_manager"),
            )
            manager_logger.info(f"{exchange_name} 거래소 연결 요청 완료")

        # 모든 거래소 연결 요청을 동시에 처리
        tasks = [
            request_connection(exchange, request_type) for exchange in exchange_names
        ]
        await asyncio.gather(*tasks)

        # 이벤트 루프 유지
        manager_logger.info("모든 거래소 연결 요청 완료, 이벤트 루프 유지 중...")
        while True:
            await asyncio.sleep(1)

    except AsyncException as e:
        manager_logger.error(f"오류: {str(e)}")
    finally:
        # 이벤트 버스 종료
        manager_logger.info("이벤트 버스 종료")
        await event_bus.stop()
        manager_logger.info("모든 거래소 연결 종료, 프로그램 종료")
