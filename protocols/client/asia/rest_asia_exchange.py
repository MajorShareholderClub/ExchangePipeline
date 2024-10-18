"""코인 Rest Resquest 설계 (국내)"""

from common.core.types import ExchangeResponseData
from common.client.market_rest.async_api_client import CoinExchangeRestClient


class OKXRest(CoinExchangeRestClient):
    def __init__(self) -> None:
        super().__init__(market="okx", location="asia")

    def _get_orderbook_url(self, coin_name: str) -> str:
        pass

    def _get_ticker_url(self, coin_name: str) -> str:
        return f"{self._rest}/market/ticker?instId={coin_name.upper()}-USDT"

    async def get_coin_all_info_price(self, coin_name: str) -> ExchangeResponseData:
        data = await super().get_coin_all_info_price(coin_name)
        return data["data"][0]


class GateIORest(CoinExchangeRestClient):
    def __init__(self) -> None:
        super().__init__(market="gateio", location="asia")

    def _get_orderbook_url(self, coin_name: str) -> str:
        pass

    def _get_ticker_url(self, coin_name: str) -> str:
        return f"{self._rest}/tickers?currency_pair={coin_name.lower()}_usdt"

    async def get_coin_all_info_price(self, coin_name: str) -> ExchangeResponseData:
        data = await super().get_coin_all_info_price(coin_name)
        return data[0]


class BybitRest(CoinExchangeRestClient):
    def __init__(self) -> None:
        super().__init__(market="bybit", location="asia")

    def _get_orderbook_url(self, coin_name: str) -> str:
        pass

    def _get_ticker_url(self, coin_name: str) -> str:
        return (
            f"{self._rest}/market/tickers?category=spot&symbol={coin_name.upper()}USDT"
        )

    async def get_coin_all_info_price(self, coin_name: str) -> ExchangeResponseData:
        data = await super().get_coin_all_info_price(coin_name)
        return data["result"]["list"][0]
