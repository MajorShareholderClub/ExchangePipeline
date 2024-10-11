from abc import ABC, abstractmethod
from typing import Callable

import asyncio


class BaseSettingWebsocket(ABC):
    """Coin Stream"""

    def __init__(
        self,
        symbol: str,
        market_env,
        market: str = "all",
    ) -> None:
        """socket 시작
        Args:
            symbol: 긁어올 코인
            market: 활성화할 마켓. Defaults to "all"이면 모든 거래소 선택.
        """
        self.market = market
        self.symbol = symbol
        self.market_env = market_env

    @abstractmethod
    def get_websocket_method(self, api: Callable) -> Callable:
        """각 자식 클래스에서 구현할 웹소켓 메서드 \n
        price_present_websocket -- orderbook_present_websocket 경로 \n
            -> korea or foreign_exchange/socket_foreign or korea_exchange.py
        """
        pass

    async def select_websocket(self) -> list:
        """마켓 선택"""
        parameter = self.market_env
        if self.market == "all":
            return [
                self.get_websocket_method(parameter[i]["api"])(self.symbol)
                for i in parameter
            ]
        else:
            return [
                self.get_websocket_method(parameter[self.market]["api"])(self.symbol)
            ]

    async def coin_present_architecture(self) -> None:
        coroutines: list = await self.select_websocket()
        await asyncio.gather(*coroutines, return_exceptions=False)


class MarketsCoinTickerPriceWebsocket(BaseSettingWebsocket):
    """티커 웹소켓"""

    def get_websocket_method(self, api: Callable) -> Callable:
        return api.price_present_websocket


class MarketsCoinOrderBookWebsocket(BaseSettingWebsocket):
    """오더북 웹소켓"""

    def get_websocket_method(self, api: Callable) -> Callable:
        return api.orderbook_present_websocket
