import asyncio

from adapters.base.event.event_bus import EventBus
from adapters.base.event.types import AsyncException, EventType
from adapters.base.event.types.event_types import (
    ConnectionRequestPayload,
    EventMetadata,
)
from common.logger import PipelineLogger
from common.registry import get_exchange, get_all_exchanges
from core.handlers.ticker import handle_ticker
from core.handlers.connection_handler import register_connection_handlers

# 파이프라인 로거 설정
manager_logger = PipelineLogger.get_logger("connection", "manager")


async def setup_event_handlers(event_bus: EventBus) -> None:
    """이벤트 핸들러 등록 함수"""
    manager_logger.info("이벤트 구독 등록")

    # 기존 핸들러 등록
    await event_bus.subscribe(EventType.MARKET_TICKER, handle_ticker)

    # 새로운 연결 관련 핸들러 등록
    await register_connection_handlers(event_bus)

    manager_logger.info("이벤트 구독 완료")


async def run_all_exchanges(exchange_names: list[str] = None) -> None:
    """모든 거래소를 동시에 실행하는 함수"""
    manager_logger.info("거래소 동시 연결 시작")

    # 이벤트 버스 초기화
    event_bus = EventBus()
    manager_logger.info("이벤트 버스 초기화")
    await event_bus.start()

    try:
        # 이벤트 핸들러 등록
        await setup_event_handlers(event_bus)

        # 지정된 거래소가 없으면 모든 거래소 실행
        if not exchange_names:
            exchange_names = list(get_all_exchanges().keys())
            manager_logger.info(
                f"모든 거래소 연결 시작 ({len(exchange_names)}개)",
                exchanges=", ".join(exchange_names),
            )
        else:
            manager_logger.info(
                f"지정된 거래소 연결 시작 ({len(exchange_names)}개)",
                exchanges=", ".join(exchange_names),
            )

        # 각 거래소에 대해 연결 요청 이벤트 발행
        for exchange_name in exchange_names:
            socket_parameter = get_exchange(exchange_name)
            if not socket_parameter:
                manager_logger.error(f"지원하지 않는 거래소: {exchange_name}")
                continue

            # 연결 요청 이벤트 발행
            await event_bus.publish(
                EventType.CONNECTION_REQUEST,
                ConnectionRequestPayload(
                    exchange_name=exchange_name,
                    parameter_info=socket_parameter["parameter_info"],
                ),
                EventMetadata(source=f"{exchange_name}_connection_manager"),
            )

        # 이벤트 루프 유지
        manager_logger.info("모든 거래소 연결 요청 완료, 이벤트 루프 유지 중...")
        while True:
            await asyncio.sleep(1)

    except AsyncException as e:
        manager_logger.error(f"예상치 못한 오류: {str(e)}")
    finally:
        # 이벤트 버스 종료
        manager_logger.info("이벤트 버스 종료")
        await event_bus.stop()
        manager_logger.info("모든 거래소 연결 종료, 프로그램 종료")
