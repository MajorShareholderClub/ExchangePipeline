from adapters.base.event.event_bus import EventBus
from adapters.base.event.types import EventType, EventPayload
from adapters.base.websocket.websocket_connection_manager import WebSocketManager
import asyncio
import logging

from test import upbithumb_socket_parameter

# 로깅 설정
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


# 구현 예시
async def main():
    # 기존 EventBus 사용
    event_bus = EventBus()

    # EventBus 시작 (중요: 배치 처리 시작)
    await event_bus.start()

    # 웹소켓 관리자 초기화 (기존 EventBus 활용)
    ws_manager = WebSocketManager(event_bus)

    # 이벤트 핸들러 등록
    async def handle_ticker(event_data: EventPayload):
        print(event_data.data)

    # 이벤트 구독
    await event_bus.subscribe(EventType.MARKET_TICKER, handle_ticker)

    # 거래소 연결
    await ws_manager.connect_exchange(
        exchange_id="upbit",
        url="wss://api.upbit.com/websocket/v1",
        headers=upbithumb_socket_parameter("BTC", "ticker"),
    )

    # 계속 실행
    while True:
        await asyncio.sleep(1)


asyncio.run(main())
