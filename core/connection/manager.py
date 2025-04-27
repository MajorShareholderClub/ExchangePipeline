import asyncio

from adapters.base.event.event_bus import EventBus
from adapters.base.event.types import EventType
from adapters.base.event.types.event_types import (
    ConnectionRequestPayload,
    EventMetadata,
)
from core.connection.retry import ConnectionRetryService, RetryConfig
from common.exceptions import AsyncException
from common.logger import PipelineLogger
from common.registry import get_exchange
from core.handlers.connection_handler import ConnectionHandlerRegistrar
from common.registry.exchanges import EXCHANGE_HANDLERS

# 핸들러에서 로깅 사용
manager_logger = PipelineLogger.get_logger("connection", "manager")


async def setup_event_handlers(event_bus: EventBus) -> None:
    """이벤트 핸들러 등록 함수"""
    # 핸들러 등록기 생성 및 초기화
    registrar = ConnectionHandlerRegistrar(event_bus)

    # ConnectionRetryService 초기화 및 핸들러 등록
    retry_service = ConnectionRetryService(
        event_bus, config=RetryConfig(max_retries=3, base_delay=1.0)
    )

    # 핸들러 등록
    await registrar.register_handlers()
    await retry_service.register_handlers()
    manager_logger.info("이벤트 핸들러 등록 완료")


async def run_all_exchanges(
    request_type: str,
    exchange_names: list[str] = None,
    symbols: list[str] = None,
) -> None:
    """모든 거래소를 동시에 실행하는 함수"""
    # 기본값 처리
    if exchange_names is None or len(exchange_names) == 0:
        # 매핑된 모든 지원 거래소 활성화

        exchange_names = list(EXCHANGE_HANDLERS.keys())

    if symbols is None:
        symbols = ["BTC_USDT", "ETH_USDT"]  # 기본 심볼 설정

    manager_logger.info("거래소 동시 연결 시작")

    # 이벤트 버스 초기화
    event_bus = EventBus()
    manager_logger.info("이벤트 버스 초기화")
    await event_bus.start()

    try:
        # 이벤트 핸들러 등록
        await setup_event_handlers(event_bus)

        # 각 거래소에 대한 연결 요청을 병렬로 처리하기 위한 함수
        async def request_connection(
            exchange_name: str, request_type: str, symbols: list[str]
        ) -> None:
            try:
                exchange_info = get_exchange(
                    exchange=exchange_name,
                    request_type=request_type,
                    symbols=symbols,
                )
                # 연결 요청 이벤트 발행
                await event_bus.publish(
                    EventType.CONNECTION_REQUEST,
                    ConnectionRequestPayload(
                        metadata=exchange_info.get("metadata", {}),
                        parameter_info=exchange_info.get("parameter_info", {}),
                        request_type=request_type,
                        socket_instance=exchange_info.get(
                            "socket_instance", exchange_info["socket_instance"]
                        ),
                        retry_count=0,
                    ),
                    EventMetadata(source=f"{exchange_name}_connection_manager"),
                )
                manager_logger.info(f"{exchange_name} 연결 요청 발행 완료")
            except ValueError as e:
                manager_logger.error(f"오류: {str(e)}")

        # 모든 거래소 연결 요청을 동시에 처리
        manager_logger.info("거래소 연결 요청 시작")
        tasks = [
            request_connection(exchange, request_type, symbols)
            for exchange in exchange_names
        ]
        await asyncio.gather(*tasks)
        manager_logger.info("모든 거래소 연결 요청 완료")

        # 이벤트 루프 유지
        manager_logger.info("이벤트 루프 시작 - Ctrl+C로 종료할 수 있습니다")
        while True:
            await asyncio.sleep(1)

    except AsyncException as e:
        manager_logger.error(f"오류: {str(e)}")

    finally:
        # 이벤트 버스 종료
        manager_logger.info("이벤트 버스 종료")
        await event_bus.stop()
        manager_logger.info("모든 거래소 연결 종료, 프로그램 종료")
