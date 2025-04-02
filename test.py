import asyncio
import logging
from typing import Any

# EDA 관련 임포트
from adapters.base.event.event_bus import EventBus
from adapters.base.event.types import EventType
from common.setting.parameter.connection_parameter import (
    bithumb_config,
    upbit_config,
    coinone_config,
    korbit_config,
    okx_config,
    gateio_config,
    bybit_config,
    binance_config,
    kraken_config,
)
from core.handlers.connections import handle_connection_event, handle_error
from core.handlers.ticker import handle_ticker
from core.exchange.connection_manager import ExchangeConnectionManager


# 로깅 설정
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("ticker_subscriber")


# fmt: off
async def run_ticker_subscribers() -> None:
    """티커 구독 실행 함수"""
    # 이벤트 버스 초기화
    event_bus = EventBus()
    await event_bus.start()

    try:
        # 이벤트 핸들러 등록
        await event_bus.subscribe(EventType.MARKET_TICKER, handle_ticker)
        await event_bus.subscribe(EventType.EXCHANGE_CONNECT, handle_connection_event)
        await event_bus.subscribe(EventType.EXCHANGE_DISCONNECT, handle_connection_event)
        await event_bus.subscribe(EventType.EXCHANGE_ERROR, handle_error)

        # 연결 관리자 초기화 (최대 5개 동시 연결)
        connection_manager = ExchangeConnectionManager(event_bus, max_workers=5)
        await connection_manager.start()
        
        # 거래소 설정 
        exchange_configs = {
            "bithumb": bithumb_config.build(),
            "upbit": upbit_config.build(),
            "coinone": coinone_config.build(),
            "korbit": korbit_config.build(),
            "okx": okx_config.build(),
            "gateio": gateio_config.build(),
            "bybit": bybit_config.build(),
            "binance": binance_config.build(),
            "kraken": kraken_config.build(),
        }
        
        # 거래소별 우선순위 설정 (주요 거래소 먼저 연결)
        priorities = {
            "binance": 10,   # 최우선
            "upbit": 20,    # 두번째 우선
            "bithumb": 30,  # 세번째 우선
            "coinone": 40,
            "korbit": 50,
            # 나머지는 기본 우선순위 100 적용
        }
        
        # 연결 작업 추가
        for exchange_name, config in exchange_configs.items():
            priority = priorities.get(exchange_name, 100)
            logger.info(f"{exchange_name} 핸들러 초기화 (우선순위: {priority})")
            await connection_manager.add_exchange(exchange_name, config, priority)

        # 모든 태스크가 완료될 때까지 대기 (실제로는 무한히 실행되어야 함)
        # 테스트를 위해 5분 후 종료하도록 설정
        await asyncio.sleep(300)  # 5분

    finally:
        # 이벤트 버스 종료
        await event_bus.stop()
        logger.info("프로그램 종료")


# 프로그램 실행
if __name__ == "__main__":
    logger.info("티커 구독 프로그램 시작")
    try:
        asyncio.run(run_ticker_subscribers())
    except KeyboardInterrupt:
        logger.info("사용자가 프로그램을 중단했습니다.")
    except Exception as e:
        logger.error(f"예상치 못한 오류: {str(e)}")
