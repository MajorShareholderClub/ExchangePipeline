"""코인 Rest Resquest 설계 (국내)"""

from common.core.types import ExchangeResponseData
from common.client.market_rest.async_api_client import CoinExchangeRestClient


class BinanceRest(CoinExchangeRestClient):
    def __init__(self) -> None:
        super().__init__(market="binance", location="ne")

    def _get_orderbook_url(self, coin_name: str) -> str:
        pass

    def _get_ticker_url(self, coin_name: str) -> str:
        return f"{self._rest}/ticker/24hr?symbol={coin_name.upper()}USDT&type=FULL"

    async def get_coin_all_info_price(self, coin_name: str) -> ExchangeResponseData:
        data = await super().get_coin_all_info_price(coin_name)
        return data


class KrakenRest(CoinExchangeRestClient):
    def __init__(self) -> None:
        super().__init__(market="kraken", location="ne")

    def _get_orderbook_url(self, coin_name: str) -> str:
        pass

    def _get_ticker_url(self, coin_name: str) -> str:
        if coin_name == "BTC":
            coin_name = "XBT"
        return f"{self._rest}/Ticker?pair={coin_name.upper()}USD"

    async def get_coin_all_info_price(self, coin_name: str) -> ExchangeResponseData:
        if coin_name == "BTC":
            coin_name = "XBT"
        data = await super().get_coin_all_info_price(coin_name)
        return data["result"][f"X{coin_name.upper()}ZUSD"]


class CoinbaseRest(CoinExchangeRestClient):
    def __init__(self) -> None:
        super().__init__(market="coinbase", location="ne")

    def _get_orderbook_url(self, coin_name: str) -> str:
        pass

    def _get_ticker_url(self, coin_name: str) -> str:
        return f"{self._rest}/products/{coin_name.upper()}-USDT/stats"

    async def get_coin_all_info_price(self, coin_name: str) -> ExchangeResponseData:
        data = await super().get_coin_all_info_price(coin_name)
        return data
