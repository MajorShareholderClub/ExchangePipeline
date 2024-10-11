import asyncio
from typing import Callable
from concurrent.futures import ThreadPoolExecutor
from pipe.connection import CoinOrderBookWebsocket, CoinPresentPriceWebsocket


connection = CoinOrderBookWebsocket | CoinPresentPriceWebsocket


# fmt: off
async def run_coin_websocket(connection_class: Callable, symbol: str, location: str) -> None:
    """지정된 웹소켓 클라이언트 클래스와 심볼을 사용하여 비동기 함수 실행."""
    websocket_client = connection_class(symbol=symbol, location=location)
    await websocket_client.coin_present_architecture()


async def coin_present_websocket(connection_class) -> None:
    """두 개의 코인 웹소켓을 동시에 실행."""
    loop = asyncio.get_running_loop()

    # 스레드 풀을 생성
    with ThreadPoolExecutor(max_workers=2) as executor:
        # run_in_executor 사용하여 비동기 작업 실행
        korea_task = loop.run_in_executor(
            executor,
            lambda: asyncio.run(run_coin_websocket(connection_class, "BTC", "korea")),
        )
        foreign_task = loop.run_in_executor(
            executor,
            lambda: asyncio.run(run_coin_websocket(connection_class, "BTC", "foreign")),
        )

        # 두 작업이 완료될 때까지 기다림
        await asyncio.gather(
            korea_task,
            foreign_task,
            return_exceptions=False,
        )


if __name__ == "__main__":
    asyncio.run(coin_present_websocket(CoinOrderBookWebsocket))