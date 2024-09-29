# import asyncio
# from concurrent.futures import ThreadPoolExecutor

# from pipe.foreign.foreign_websocket_client import ForeignCoinPresentPriceWebsocket
# from pipe.korea.korea_websocket_client import KoreaCoinPresentPriceWebsocket


# # ForeignCoinPresentPriceWebsocket("BTC") 비동기 함수 실행
# def run_foreign_coin_websocket():
#     loop = asyncio.new_event_loop()  # 스레드별로 event loop 생성
#     asyncio.set_event_loop(loop)
#     loop.run_until_complete(
#         ForeignCoinPresentPriceWebsocket("BTC").coin_present_architecture()
#     )
#     loop.close()


# # KoreaCoinPresentPriceWebsocket("BTC") 비동기 함수 실행
# def run_korea_coin_websocket():
#     loop = asyncio.new_event_loop()  # 스레드별로 event loop 생성
#     asyncio.set_event_loop(loop)
#     loop.run_until_complete(
#         KoreaCoinPresentPriceWebsocket("BTC").coin_present_architecture()
#     )
#     loop.close()


# async def coin_present_websocket() -> None:
#     loop = asyncio.get_running_loop()

#     # with 문으로 ThreadPoolExecutor를 안전하게 관리
#     with ThreadPoolExecutor(max_workers=2) as executor:
#         foreign_task = loop.run_in_executor(executor, run_foreign_coin_websocket)
#         korea_task = loop.run_in_executor(executor, run_korea_coin_websocket)

#         # 두 작업이 완료될 때까지 기다림
#         await asyncio.gather(foreign_task, korea_task, return_exceptions=False)


# if __name__ == "__main__":
#     asyncio.run(coin_present_websocket())
"""
실시간 테스트
"""

import asyncio

from pipe.korea.korea_rest_client import KoreaExchangeRestAPI
from pipe.foreign.foreign_rest_client import ForeignExchangeRestAPI


async def f_btc_present_start() -> None:
    """
    bitcoin kafak stream
    """
    await ForeignExchangeRestAPI().total_pull_request("BTC")


async def k_btc_present_start() -> None:
    """
    ethereum kafak stream
    """
    await KoreaExchangeRestAPI().total_pull_request("BTC")


async def be_present_gether() -> None:
    """
    kafka async stream
    """
    tasks = [
        asyncio.create_task(f_btc_present_start()),
        asyncio.create_task(k_btc_present_start()),
    ]
    await asyncio.gather(*tasks, return_exceptions=False)


async def data_sending_start() -> None:
    await be_present_gether()


if __name__ == "__main__":
    asyncio.run(be_present_gether())
