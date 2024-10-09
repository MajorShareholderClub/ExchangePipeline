"""
Socket Test
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from pipe.connection import CoinPresentPriceWebsocket

socket = CoinPresentPriceWebsocket


def run_coin_websocket(
    client_class: CoinPresentPriceWebsocket, symbol: str, location: str
):
    """지정된 웹소켓 클라이언트 클래스와 심볼을 사용하여 비동기 함수 실행."""
    loop = asyncio.new_event_loop()  # 스레드별로 event loop 생성
    asyncio.set_event_loop(loop)
    loop.run_until_complete(
        client_class(symbol=symbol, location=location).coin_present_architecture()
    )
    loop.close()


async def coin_present_websocket() -> None:
    """두 개의 코인 웹소켓을 동시에 실행."""
    loop = asyncio.get_running_loop()

    with ThreadPoolExecutor(max_workers=4) as executor:
        # 클라이언트 클래스를 매개변수로 전달하여 작업 실행
        korea_task_ticker = loop.run_in_executor(
            executor, run_coin_websocket, CoinPresentPriceWebsocket, "BTC", "korea"
        )
        foreign_task_ticker = loop.run_in_executor(
            executor, run_coin_websocket, CoinPresentPriceWebsocket, "BTC", "foreign"
        )

        # 두 작업이 완료될 때까지 기다림
        await asyncio.gather(
            korea_task_ticker, foreign_task_ticker, return_exceptions=False
        )


if __name__ == "__main__":
    asyncio.run(coin_present_websocket())
