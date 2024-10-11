from abc import ABC, abstractmethod
from typing import Callable

import asyncio
from common.core.types import SubScribeFormat
from common.core.abstract import AbstractExchangeSocketClient
from common.utils.other_utils import get_symbol_collect_url
from common.client.market_socket.websocket_interface import (
    WebsocketConnectionManager as WCM,
)
from config.yml_param_load import SocketMarketLoader


class BaseSettingWebsocket(ABC):
    """Coin Stream"""

    def __init__(
        self,
        location: str,
        symbol: str,
        market: str = "all",
    ) -> None:
        """socket 시작
        Args:
            symbol: 긁어올 코인
            market: 활성화할 마켓. Defaults to "all"이면 모든 거래소 선택.
        """
        self.market = market
        self.symbol = symbol
        self.market_env = SocketMarketLoader(location).process_market_info()

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


class CoinExchangeSocketClient(AbstractExchangeSocketClient):
    def __init__(
        self, target: str, socket_parameter: Callable[[str], SubScribeFormat]
    ) -> None:
        self._websocket = get_symbol_collect_url(target, "socket")
        self.socket_parameter = socket_parameter
        self.ticker = "ticker"
        self.orderbook = "orderbook"

    # fmt: off
    async def get_present_websocket(self, symbol: str, req_type: str) -> None:
        """소켓 출발점"""
        return await WCM().websocket_to_json(
            uri=self._websocket,
            subs_fmt=self.socket_parameter(symbol=symbol, req_type=req_type),
            symbol=symbol,
            socket_type=req_type
        )
