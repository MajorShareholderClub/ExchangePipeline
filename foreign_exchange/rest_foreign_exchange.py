"""코인 Rest Resquest 설계 (국내)"""

from common.core.types import ExchangeResponseData
from common.client.market_rest.async_api_client import CoinExchangeRestClient


class BinanceRest(CoinExchangeRestClient):
    def __init__(self) -> None:
        super().__init__(market="binance")

    def _get_orderbook_url(self, coin_name: str) -> str:
        pass

    def _get_ticker_url(self, coin_name: str) -> str:
        return f"{self._rest}/ticker/24hr?symbol={coin_name.upper()}USDT&type=FULL"

    async def get_coin_all_info_price(self, coin_name: str) -> ExchangeResponseData:
        data = await super().get_coin_all_info_price(coin_name)
        return data


class KrakenRest(CoinExchangeRestClient):
    def __init__(self) -> None:
        super().__init__(market="kraken")

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


class OKXRest(CoinExchangeRestClient):
    def __init__(self) -> None:
        super().__init__(market="okx")

    def _get_orderbook_url(self, coin_name: str) -> str:
        pass

    def _get_ticker_url(self, coin_name: str) -> str:
        return f"{self._rest}/market/ticker?instId={coin_name.upper()}-USDT"

    async def get_coin_all_info_price(self, coin_name: str) -> ExchangeResponseData:
        data = await super().get_coin_all_info_price(coin_name)
        return data["data"][0]


class GateIORest(CoinExchangeRestClient):
    def __init__(self) -> None:
        super().__init__(market="gateio")

    def _get_orderbook_url(self, coin_name: str) -> str:
        pass

    def _get_ticker_url(self, coin_name: str) -> str:
        return f"{self._rest}/tickers?currency_pair={coin_name.lower()}_usdt"

    async def get_coin_all_info_price(self, coin_name: str) -> ExchangeResponseData:
        data = await super().get_coin_all_info_price(coin_name)
        return data[0]


class BybitRest(CoinExchangeRestClient):
    def __init__(self) -> None:
        super().__init__(market="bybit")

    def _get_orderbook_url(self, coin_name: str) -> str:
        pass

    def _get_ticker_url(self, coin_name: str) -> str:
        return (
            f"{self._rest}/market/tickers?category=spot&symbol={coin_name.upper()}USDT"
        )

    async def get_coin_all_info_price(self, coin_name: str) -> ExchangeResponseData:
        data = await super().get_coin_all_info_price(coin_name)
        return data["result"]["list"][0]
