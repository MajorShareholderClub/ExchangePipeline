"""
코인 정보 추상화
"""

from common.utils.other_utils import get_symbol_collect_url
from common.core.abstract import AbstractExchangeSocketClient
from common.setting.socket_parameter import (
    upbithumb_socket_parameter,
    coinone_socket_parameter,
)


class UpbitSocket(AbstractExchangeSocketClient):
    def __init__(self) -> None:
        self._websocket = get_symbol_collect_url("upbit", "socket")

    async def get_present_websocket(self, symbol: str) -> None:
        from pipe.korea_exchange.websocket_client import (
            WebsocketConnectionManager as WCM,
        )

        return await WCM().websocket_to_json(
            uri=self._websocket,
            subs_fmt=upbithumb_socket_parameter(symbol=symbol),
            symbol=symbol,
        )


class BithumbSocket(AbstractExchangeSocketClient):
    def __init__(self) -> None:
        self._websocket = get_symbol_collect_url("bithumb", "socket")

    async def get_present_websocket(self, symbol: str) -> None:
        from pipe.korea_exchange.websocket_client import (
            WebsocketConnectionManager as WCM,
        )

        return await WCM().websocket_to_json(
            uri=self._websocket,
            subs_fmt=upbithumb_socket_parameter(symbol=symbol),
            symbol=symbol,
        )


class CoinoneSocket(AbstractExchangeSocketClient):
    def __init__(self) -> None:
        self._websocket = get_symbol_collect_url("coinone", "socket")

    async def get_present_websocket(self, symbol: str) -> None:
        from pipe.korea_exchange.websocket_client import (
            WebsocketConnectionManager as WCM,
        )

        return await WCM().websocket_to_json(
            uri=self._websocket,
            subs_fmt=coinone_socket_parameter(symbol=symbol),
            symbol=symbol,
        )
