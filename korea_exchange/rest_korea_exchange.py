"""코인 Rest Resquest 설계 (국내)"""

from abc import abstractmethod
from common.utils.other_utils import get_symbol_collect_url
from common.client.async_api_client import AsyncRequestJSON
from common.core.abstract import AbstractExchangeRestClient
from common.core.types import ExchangeResponseData


async def async_request_data(url: str) -> ExchangeResponseData:
    """비동기 호출 함수"""
    return await AsyncRequestJSON(
        url=url, headers={"Accept": "application/json"}
    ).async_fetch_json()


class CoinExchangeRestClient(AbstractExchangeRestClient):
    def __init__(self, market: str) -> None:
        self.market = market
        self._rest = get_symbol_collect_url(market=market, type_="rest")

    async def get_coin_all_info_price(self, coin_name: str) -> ExchangeResponseData:
        """
        Subject:
            - upbithumb 코인 현재가\n
        Parameter:
            - coin_name (str) : 코인이름\n
        Returns:
            >>>  {
                'market': 'KRW-BTC',
                'trade_date': '20230717',
                'trade_time': '090305',
                ...
            }
        """
        data = async_request_data(url=self._get_ticker_url(coin_name))
        return await data

    @abstractmethod
    def _get_orderbook_url(self, coin_name: str) -> str:
        """ordering 주소"""
        pass

    @abstractmethod
    def _get_ticker_url(self, coin_name: str) -> str:
        """ticker 주소"""
        pass


class UpbitRest(CoinExchangeRestClient):
    def __init__(self) -> None:
        super().__init__("upbit")

    def _get_orderbook_url(self, coin_name: str) -> str:
        return f"{self._rest}/orderbook?level=0&markets=KRW-{coin_name.upper()}"

    def _get_ticker_url(self, coin_name: str) -> str:
        return f"{self._rest}/ticker?markets=KRW-{coin_name.upper()}"

    async def get_coin_all_info_price(self, coin_name: str) -> ExchangeResponseData:
        data = await super().get_coin_all_info_price(coin_name)
        return data[0]


class BithumbRest(CoinExchangeRestClient):
    def __init__(self) -> None:
        super().__init__("bithumb")

    def _get_orderbook_url(self, coin_name: str) -> str:
        return f"{self._rest}/orderbook?level=0&markets=KRW-{coin_name.upper()}"

    def _get_ticker_url(self, coin_name: str) -> str:
        return f"{self._rest}/ticker?markets=KRW-{coin_name.upper()}"

    async def get_coin_all_info_price(self, coin_name: str) -> ExchangeResponseData:
        data = await super().get_coin_all_info_price(coin_name)
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
        return data["data"][0]
