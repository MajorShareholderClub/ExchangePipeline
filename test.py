import asyncio
from pipe.foreign.foreign_websocket_client import ForeignCoinPresentPriceWebsocket
from pipe.korea.korea_websocket_client import KoreaCoinPresentPriceWebsocket


async def coin_present_websocket_btc() -> None:
    await ForeignCoinPresentPriceWebsocket("BTC").coin_present_architecture()


async def coin_present_websocket_TT() -> None:
    await KoreaCoinPresentPriceWebsocket("BTC").coin_present_architecture()


async def coin_present_websocket() -> None:
    task = [
        asyncio.create_task(coin_present_websocket_btc()),
        # asyncio.create_task(coin_present_websocket_TT()),
    ]
    await asyncio.gather(*task, return_exceptions=False)


if __name__ == "__main__":
    asyncio.run(coin_present_websocket())
# """
# 실시간 테스트
# """

# import asyncio

# from pipe.korea.korea_rest_client import KoreaExchangeRestAPI
# from pipe.foreign.foreign_rest_client import ForeignExchangeRestAPI


# async def f_btc_present_start() -> None:
#     """
#     bitcoin kafak stream
#     """
#     await ForeignExchangeRestAPI().total_pull_request("ETH")


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
