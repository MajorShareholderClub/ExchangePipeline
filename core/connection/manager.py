import asyncio
import logging

from adapters.base.event.event_bus import EventBus
from adapters.base.event.types import AsyncException, EventType
from adapters.exchange import WorldWebSocket
from common.logger import PipelineLogger
from common.registry import get_exchange, get_all_exchanges
from core.handlers.connections import handle_connection_event, handle_error
from core.handlers.ticker import handle_ticker

from .decorator import RetryConnectionDecorator

# 파이프라인 로거 설정
manager_logger = PipelineLogger.get_logger("connection", "manager")


async def run_ticker(event_bus: EventBus) -> None:
    manager_logger.info("이벤트 구독 등록")
    await event_bus.subscribe(EventType.MARKET_TICKER, handle_ticker)
    await event_bus.subscribe(EventType.EXCHANGE_CONNECT, handle_connection_event)
    await event_bus.subscribe(EventType.EXCHANGE_DISCONNECT, handle_connection_event)
    await event_bus.subscribe(EventType.EXCHANGE_ERROR, handle_error)
    manager_logger.info("이벤트 구독 완료")


async def connect_exchange(
    event_bus: EventBus, exchange_name: str, use_decorators: bool = True
) -> None:
    """단일 거래소 연결 함수"""
    manager_logger.set_context(exchange=exchange_name)

    socket_parameter = get_exchange(exchange_name)
    if not socket_parameter:
        manager_logger.error(f"지원하지 않는 거래소: {exchange_name}")
        return

    connection_manager: WorldWebSocket = socket_parameter["socket"](
        event_bus, exchange_name=exchange_name
    )

    # 데코레이터 패턴 적용
    if use_decorators:
        manager_logger.info(
            f"재연결 데코레이터 적용", decorator="RetryConnectionDecorator"
        )
        connection_manager = RetryConnectionDecorator(
            connection_manager, exchange_name=exchange_name
        )

    try:
        manager_logger.info(f"거래소 연결 시작", url=socket_parameter["url"])
        await connection_manager.connect_and_subscribe(socket_parameter["url"])
        manager_logger.info(f"{exchange_name} 거래소 연결 성공")
    except AsyncException as e:
        manager_logger.error(f"{exchange_name} 거래소 연결 실패: {str(e)}")


async def run_all_exchanges(exchange_names: list[str] = None) -> None:
    """모든 거래소를 동시에 실행하는 함수"""
    manager_logger.info("거래소 동시 연결 시작")

    # 이벤트 버스 초기화
    event_bus = EventBus()
    manager_logger.info("이벤트 버스 초기화")
    await event_bus.start()

    try:
        await run_ticker(event_bus)

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

        # 비동기로 모든 거래소 연결 시작
        connection_tasks = [
            asyncio.create_task(connect_exchange(event_bus, exchange_name))
            for exchange_name in exchange_names
        ]

        # 모든 연결 작업 완료 대기
        manager_logger.info("모든 거래소 연결 대기 중...")
        await asyncio.gather(*connection_tasks)
        manager_logger.info("모든 거래소 연결 완료")

    except AsyncException as e:
        manager_logger.error(f"예상치 못한 오류: {str(e)}")
    finally:
        # 이벤트 버스 종료
        manager_logger.info("이벤트 버스 종료")
        await event_bus.stop()
        manager_logger.info("모든 거래소 연결 종료, 프로그램 종료")
