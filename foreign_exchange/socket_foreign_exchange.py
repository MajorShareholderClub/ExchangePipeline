"""
코인 정보 추상화
"""

from typing import Callable
from common.utils.other_utils import get_symbol_collect_url
from common.core.abstract import AbstractExchangeSocketClient
from common.core.types import SubScribeFormat
from common.setting.socket_parameter import (
    binance_socket_paramater,
    kraken_socket_parameter,
    okx_socket_parameter,
    gateio_socket_parameter,
    bybit_socket_parameter,
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
        from pipe.foreign.foreign_websocket_client import (
            ForeignWebsocketConnection as WCM
        )

        return await WCM().websocket_to_json(
            uri=self._websocket,
            subs_fmt=self.socket_parameter(symbol=symbol, req_type=req_type),
            symbol=symbol,
            socket_type=socket_type
        )


class BinanceSocket(CoinExchangeSocketClient):
    def __init__(self) -> None:
        super().__init__(target="binance", socket_parameter=binance_socket_paramater)

    async def price_present_websocket(self, symbol: str) -> None:
        return await super().get_present_websocket(
            symbol, req_type="ticker", socket_type=self.ticker
        )

    async def orderbook_present_websocket(self, symbol: str) -> None:
        return await super().get_present_websocket(
            symbol, req_type="depth20", socket_type=self.orderbook
        )


class KrakenSocket(CoinExchangeSocketClient):
    def __init__(self) -> None:
        super().__init__(target="kraken", socket_parameter=kraken_socket_parameter)

    async def price_present_websocket(self, symbol: str) -> None:
        return await super().get_present_websocket(
            symbol, req_type="ticker", socket_type=self.ticker
        )

    async def orderbook_present_websocket(self, symbol: str) -> None:
        return await super().get_present_websocket(
            symbol, req_type="book", socket_type=self.orderbook
        )


class GateIOSocket(CoinExchangeSocketClient):
    def __init__(self) -> None:
        super().__init__(target="gateio", socket_parameter=gateio_socket_parameter)

    async def price_present_websocket(self, symbol: str) -> None:
        return await super().get_present_websocket(
            symbol, req_type="tickers", socket_type=self.ticker
        )

    async def orderbook_present_websocket(self, symbol: str) -> None:
        return await super().get_present_websocket(
            symbol, req_type="order_book", socket_type=self.orderbook
        )


class OKXSocket(CoinExchangeSocketClient):
    def __init__(self) -> None:
        super().__init__(target="okx", socket_parameter=okx_socket_parameter)

    async def price_present_websocket(self, symbol: str) -> None:
        return await super().get_present_websocket(
            symbol, req_type="tickers", socket_type=self.ticker
        )

    async def orderbook_present_websocket(self, symbol: str) -> None:
        return await super().get_present_websocket(
            symbol, req_type="books", socket_type=self.orderbook
        )


class ByBitSocket(CoinExchangeSocketClient):
    def __init__(self) -> None:
        super().__init__(target="bybit", socket_parameter=bybit_socket_parameter)

    async def price_present_websocket(self, symbol: str) -> None:
        return await super().get_present_websocket(
            symbol, req_type="tickers", socket_type=self.ticker
        )

    async def orderbook_present_websocket(self, symbol: str) -> None:
        return await super().get_present_websocket(
            symbol, req_type="orderbook", socket_type=self.orderbook
        )
