import asyncio
from concurrent.futures import ThreadPoolExecutor

from pipe.foreign.foreign_websocket_client import ForeignCoinPresentPriceWebsocket
from pipe.korea.korea_websocket_client import KoreaCoinPresentPriceWebsocket


socket = KoreaCoinPresentPriceWebsocket | ForeignCoinPresentPriceWebsocket


def run_coin_websocket(client_class: socket, symbol: str):
    """지정된 웹소켓 클라이언트 클래스와 심볼을 사용하여 비동기 함수 실행."""
    loop = asyncio.new_event_loop()  # 스레드별로 event loop 생성
    asyncio.set_event_loop(loop)
    loop.run_until_complete(client_class(symbol=symbol).coin_present_architecture())
    loop.close()


async def coin_present_websocket() -> None:
    """두 개의 코인 웹소켓을 동시에 실행."""
    loop = asyncio.get_running_loop()

    with ThreadPoolExecutor(max_workers=2) as executor:
        # 클라이언트 클래스를 매개변수로 전달하여 작업 실행
        foreign_task = loop.run_in_executor(
            executor, run_coin_websocket, ForeignCoinPresentPriceWebsocket, "BTC"
        )
        korea_task = loop.run_in_executor(
            executor, run_coin_websocket, KoreaCoinPresentPriceWebsocket, "BTC"
        )

        # 두 작업이 완료될 때까지 기다림
        await asyncio.gather(foreign_task, korea_task)


if __name__ == "__main__":
    asyncio.run(coin_present_websocket())
"""
실시간 테스트
"""

# import asyncio

# from pipe.korea.korea_rest_client import KoreaExchangeRestAPI
# from pipe.foreign.foreign_rest_client import ForeignExchangeRestAPI


# async def f_btc_present_start() -> None:
#     """
#     bitcoin kafak stream
#     """
#     await ForeignExchangeRestAPI().total_pull_request("BTC")


# async def k_btc_present_start() -> None:
#     """
#     ethereum kafak stream
#     """
#     await KoreaExchangeRestAPI().total_pull_request("BTC")


# async def be_present_gether() -> None:
#     """
#     kafka async stream
#     """
#     tasks = [
#         asyncio.create_task(f_btc_present_start()),
#         asyncio.create_task(k_btc_present_start()),
#     ]
#     await asyncio.gather(*tasks, return_exceptions=False)


# async def data_sending_start() -> None:
#     await be_present_gether()


# if __name__ == "__main__":
#     asyncio.run(be_present_gether())
