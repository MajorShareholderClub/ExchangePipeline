"""코인 Rest Resquest 설계 (국내)"""

import tracemalloc

tracemalloc.start()

from common.client.market_rest.async_api_client import CoinExchangeRestClient
from common.core.types import ExchangeResponseData


class UpbitRest(CoinExchangeRestClient):
    def __init__(self) -> None:
        super().__init__(market="upbit")

    def _get_orderbook_url(self, coin_name: str) -> str:
        return f"{self._rest}/orderbook?level=0&markets=KRW-{coin_name.upper()}"

    def _get_ticker_url(self, coin_name: str) -> str:
        return f"{self._rest}/ticker?markets=KRW-{coin_name.upper()}"

    async def get_coin_all_info_price(self, coin_name: str) -> ExchangeResponseData:
        data = await super().get_coin_all_info_price(coin_name)
        if data is None:
            return None
        return data[0]


class BithumbRest(CoinExchangeRestClient):
    def __init__(self) -> None:
        super().__init__(market="bithumb")

    def _get_orderbook_url(self, coin_name: str) -> str:
        return f"{self._rest}/orderbook?level=0&markets=KRW-{coin_name.upper()}"

    def _get_ticker_url(self, coin_name: str) -> str:
        return f"{self._rest}/ticker?markets=KRW-{coin_name.upper()}"

    async def get_coin_all_info_price(self, coin_name: str) -> ExchangeResponseData:
        data = await super().get_coin_all_info_price(coin_name)
        if data is None:
            return None
        return data[0]


class CoinoneRest(CoinExchangeRestClient):
    def __init__(self) -> None:
        super().__init__(market="coinone")

    def _get_orderbook_url(self, coin_name: str) -> str:
        return f"{self._rest}/orderbook/KRW/{coin_name.upper()}?size=15"

    def _get_ticker_url(self, coin_name: str) -> str:
        return f"{self._rest}/ticker_new/KRW/{coin_name.upper()}?additional_data=true"

    async def get_coin_all_info_price(self, coin_name: str) -> ExchangeResponseData:
        data = await super().get_coin_all_info_price(coin_name)
        if data is None:
            return None
        return data["tickers"][0]


class KorbitRest(CoinExchangeRestClient):
    def __init__(self) -> None:
        super().__init__(market="korbit")

    def _get_orderbook_url(self, coin_name: str) -> str:
        return f"{self._rest}/orderbook?symbol={coin_name.lower()}_krw"

    def _get_ticker_url(self, coin_name: str) -> str:
        return f"{self._rest}/tickers?symbol={coin_name.lower()}_krw"

    async def get_coin_all_info_price(self, coin_name: str) -> ExchangeResponseData:
        data = await super().get_coin_all_info_price(coin_name)
        if data is None:
            return None
        return data["data"][0]
