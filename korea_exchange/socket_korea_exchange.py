"""
코인 정보 추상화
"""

from typing import Callable, Coroutine, Any
from common.utils.other_utils import get_symbol_collect_url
from common.core.abstract import AbstractExchangeSocketClient
from common.setting.socket_parameter import (
    upbithumb_socket_parameter,
    coinone_socket_parameter,
)

from common.core.types import SubScribeFormat


class CoinExchangeSocketClient(AbstractExchangeSocketClient):
    def __init__(
        self, target: str, socket_parameter: Callable[[str], SubScribeFormat]
    ) -> None:
        self._websocket = get_symbol_collect_url(target, "socket")
        self.socket_parameter = socket_parameter

    # fmt: off
    async def get_present_websocket(self, symbol: str, req_type: str) -> Coroutine[Any, Any, None]:
        from pipe.korea.websocket_client import (
            WebsocketConnectionManager as WCM
        )

        return await WCM().websocket_to_json(
            uri=self._websocket,
            subs_fmt=self.socket_parameter(symbol=symbol, req_type=req_type),
            symbol=symbol,
        )


class UpbitSocket(CoinExchangeSocketClient):
    def __init__(self) -> None:
        super().__init__(target="upbit", socket_parameter=upbithumb_socket_parameter)

    async def get_present_websocket(
        self, symbol: str
    ) -> Coroutine[Any, Any, Coroutine[Any, Any, None]]:
        return await super().get_present_websocket(symbol, req_type="ticker")


class BithumbSocket(CoinExchangeSocketClient):
    def __init__(self) -> None:
        super().__init__(target="bithumb", socket_parameter=upbithumb_socket_parameter)

    async def get_present_websocket(self, symbol: str) -> Coroutine[Any, Any, None]:
        return await super().get_present_websocket(symbol, req_type="ticker")


class CoinoneSocket(CoinExchangeSocketClient):
    def __init__(self) -> None:
        super().__init__(target="coinone", socket_parameter=coinone_socket_parameter)

    async def get_present_websocket(self, symbol: str) -> Coroutine[Any, Any, None]:
        return await super().get_present_websocket(symbol, req_type="ticker")
