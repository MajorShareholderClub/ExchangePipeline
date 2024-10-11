"""
코인 정보 추상화
"""

from typing import Callable
from common.core.abstract import AbstractExchangeSocketClient
from common.utils.other_utils import get_symbol_collect_url
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
        self.ticker = "ticker"
        self.orderbook = "orderbook"

    # fmt: off
    async def get_present_websocket(self, symbol: str, req_type: str, socket_type: str) -> None:
        from pipe.korea.korea_websocket_client import KoreaWebsocketConnection as WCM

        """소켓 출발점"""
        return await WCM().websocket_to_json(
            uri=self._websocket,
            subs_fmt=self.socket_parameter(symbol=symbol, req_type=req_type),
            symbol=symbol,
            socket_type=socket_type
        )


class UpbitSocket(CoinExchangeSocketClient):
    def __init__(self) -> None:
        super().__init__(target="upbit", socket_parameter=upbithumb_socket_parameter)

    async def price_present_websocket(self, symbol: str) -> None:
        return await super().get_present_websocket(
            symbol, req_type="ticker", socket_type=self.ticker
        )

    async def orderbook_present_websocket(self, symbol: str) -> None:
        return await super().get_present_websocket(
            symbol, req_type="orderbook", socket_type=self.orderbook
        )


class BithumbSocket(CoinExchangeSocketClient):
    def __init__(self) -> None:
        super().__init__(target="bithumb", socket_parameter=upbithumb_socket_parameter)

    async def price_present_websocket(self, symbol: str) -> None:
        return await super().get_present_websocket(
            symbol, req_type="ticker", socket_type=self.ticker
        )

    async def orderbook_present_websocket(self, symbol: str) -> None:
        return await super().get_present_websocket(
            symbol, req_type="orderbook", socket_type=self.orderbook
        )


class CoinoneSocket(CoinExchangeSocketClient):
    def __init__(self) -> None:
        super().__init__(target="coinone", socket_parameter=coinone_socket_parameter)

    async def price_present_websocket(self, symbol: str) -> None:
        return await super().get_present_websocket(
            symbol, req_type="ticker", socket_type=self.ticker
        )

    async def orderbook_present_websocket(self, symbol: str) -> None:
        return await super().get_present_websocket(
            symbol, req_type="orderbook", socket_type=self.orderbook
        )


class KorbitSocket(CoinExchangeSocketClient):
    def __init__(self) -> None:
        super().__init__(target="korbit", socket_parameter=korbit_socket_parameter)

    async def price_present_websocket(self, symbol: str) -> None:
        return await super().get_present_websocket(
            symbol, req_type="ticker", socket_type=self.ticker
        )

    async def orderbook_present_websocket(self, symbol: str) -> None:
        return await super().get_present_websocket(
            symbol, req_type="orderbook", socket_type=self.orderbook
        )
