"""
Rest Test
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
