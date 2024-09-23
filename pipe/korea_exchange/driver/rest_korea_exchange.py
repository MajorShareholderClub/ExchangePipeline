"""
코인 정보 추상화
"""

from common.utils.other_utils import get_symbol_collect_url
from common.driver.rest_driver import AsyncRequestJSON
from common.core.abstract import AbstractExchangeRestClient
from common.core.types import ExchangeResponseData


async def async_request_data(url: str) -> ExchangeResponseData:
    """비동기 호출 함수"""
    return await AsyncRequestJSON(
        url=url, headers={"Accept": "application/json"}
    ).async_fetch_json()


class UpbitRest(AbstractExchangeRestClient):
    def __init__(self) -> None:
        self._rest = get_symbol_collect_url("upbit", "rest")

    async def get_coin_all_orderbook(self, coin_name: str) -> dict[str, int]:
        data = await async_request_data(
            url=f"{self._rest}/orderbook?level=0&markets=KRW-{coin_name.upper()}"
        )
        order = data[0]["orderbook_units"]

        max_ask_price = max(item["ask_price"] for item in order)
        min_bid_price = min(item["bid_price"] for item in order)

        return {"ask": max_ask_price, "bid": min_bid_price}

    async def get_coin_all_info_price(self, coin_name: str) -> ExchangeResponseData:
        """
        Subject:
            - upbit 코인 현재가\n
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
        data = await async_request_data(
            url=f"{self._rest}/ticker?markets=KRW-{coin_name.upper()}"
        )
        return data[0]


class BithumbRest(AbstractExchangeRestClient):
    def __init__(self) -> None:
        self._rest = get_symbol_collect_url("bithumb", "rest")

    async def get_coin_all_orderbook(self, coin_name: str) -> dict[str, int]:
        data = await async_request_data(
            url=f"{self._rest}/orderbook?markets=KRW-{coin_name.upper()}"
        )
        order = data[0]["orderbook_units"]

        max_ask_price = max(item["ask_price"] for item in order)
        min_bid_price = min(item["bid_price"] for item in order)
        return {"ask": max_ask_price, "bid": min_bid_price}

    async def get_coin_all_info_price(self, coin_name: str) -> ExchangeResponseData:
        """
        Subject:
            - bithum 코인 현재가\n
        Parameter:
            - coin_name (str) : 코인이름\n
        Returns:
            >>> {
                'opening_price': '39067000',
                'closing_price': '38770000',
                'min_price': '38672000',
                'max_price': '39085000',
                ...
            }
        """
        # fmt: off
        data = await async_request_data(
            url=f"{self._rest}/ticker?markets=KRW-{coin_name.upper()}"
        )
        return data[0]


class CoinoneRest(AbstractExchangeRestClient):
    def __init__(self) -> None:
        self._rest = get_symbol_collect_url("coinone", "rest")

    async def get_coin_all_orderbook(self, coin_name: str) -> dict[str, int]:
        data = await async_request_data(
            url=f"{self._rest}/orderbook/KRW/{coin_name.upper()}?size=15"
        )
        max_ask_price = max(item["price"] for item in data["asks"])
        min_bid_price = min(item["price"] for item in data["bids"])

        return {"ask": max_ask_price, "bid": min_bid_price}

    async def get_coin_all_info_price(self, coin_name: str) -> ExchangeResponseData:
        """
        Subject:
            - coinone 코인 현재가 추출\n
        Parameter:
            - coin_name (str) : 코인이름\n
        Returns:
            >>> {
                "quote_currency": "KRW",
                "target_currency": "BTC",
                "timestamp": 1499341142000,
                "high": "3845000.0",
                "low": "3819000.0",
                ...
            }
        """
        data = await async_request_data(
            url=f"{self._rest}/ticker_new/KRW/{coin_name.upper()}?additional_data=true"
        )
        return data["tickers"][0]


class KorbitRest(AbstractExchangeRestClient):
    def __init__(self) -> None:
        self._rest = get_symbol_collect_url("korbit", "rest")

    async def get_coin_all_orderbook(self, coin_name: str) -> dict[str, int]:
        data = await async_request_data(
            url=f"{self._rest}/orderbook?currency_pair={coin_name.lower()}_krw"
        )
        max_ask_price = max(item[0] for item in data["asks"])
        min_bid_price = min(item[0] for item in data["bids"])

        return {"ask": max_ask_price, "bid": min_bid_price}

    async def get_coin_all_info_price(self, coin_name: str) -> ExchangeResponseData:
        """
        Subject:
            - korbit 코인 현재가 추출\n
        Parameter:
            - coin_name (str) : 코인이름\n
        Returns:
            >>> {
                "timestamp": 1689595134649,
                "last": "38809000",
                "open": "38932000",
                "bid": "38808000",
                ...
            }
        """
        return await async_request_data(
            url=f"{self._rest}/ticker/detailed?currency_pair={coin_name.lower()}_krw"
        )
