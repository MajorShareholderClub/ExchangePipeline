"""
코인 정보 추상화
"""

from typing import Callable
from common.utils.other_utils import get_symbol_collect_url
from common.core.abstract import AbstractExchangeSocketClient
from common.core.types import SubScribeFormat
from common.setting.socket_parameter import (
    upbithumb_socket_parameter,
    coinone_socket_parameter,
    korbit_socket_parameter,
)


class CoinExchangeSocketClient(AbstractExchangeSocketClient):
    def __init__(
        self, target: str, socket_parameter: Callable[[str], SubScribeFormat]
    ) -> None:
        self._websocket = get_symbol_collect_url(target, "socket")
        self.socket_parameter = socket_parameter

    # fmt: off
    async def get_present_websocket(self, symbol: str, req_type: str) -> None:
        from pipe.korea.korea_websocket_client import (
            KoreaWebsocketConnection as WCM
        )

        return await WCM().websocket_to_json(
            uri=self._websocket,
            subs_fmt=self.socket_parameter(symbol=symbol, req_type=req_type),
            symbol=symbol,
        )


class UpbitSocket(CoinExchangeSocketClient):
    def __init__(self) -> None:
        super().__init__(target="upbit", socket_parameter=upbithumb_socket_parameter)

    async def price_present_websocket(self, symbol: str) -> None:
        return await super().get_present_websocket(symbol, req_type="ticker")

    async def orderbook_present_websocket(self, symbol: str) -> None:
        return await super().get_present_websocket(symbol, req_type="orderbook")


class BithumbSocket(CoinExchangeSocketClient):
    def __init__(self) -> None:
        super().__init__(target="bithumb", socket_parameter=upbithumb_socket_parameter)

    async def price_present_websocket(self, symbol: str) -> None:
        return await super().get_present_websocket(symbol, req_type="ticker")

    async def orderbook_present_websocket(self, symbol: str) -> None:
        return await super().get_present_websocket(symbol, req_type="orderbook")


class CoinoneSocket(CoinExchangeSocketClient):
    def __init__(self) -> None:
        super().__init__(target="coinone", socket_parameter=coinone_socket_parameter)

    async def price_present_websocket(self, symbol: str) -> None:
        return await super().get_present_websocket(symbol, req_type="ticker")

    async def orderbook_present_websocket(self, symbol: str) -> None:
        return await super().get_present_websocket(symbol, req_type="orderbook")


class KorbitSocket(CoinExchangeSocketClient):
    def __init__(self) -> None:
        super().__init__(target="korbit", socket_parameter=korbit_socket_parameter)

    async def price_present_websocket(self, symbol: str) -> None:
        return await super().get_present_websocket(symbol, req_type="ticker")

    async def orderbook_present_websocket(self, symbol: str) -> None:
        return await super().get_present_websocket(symbol, req_type="orderbook")
