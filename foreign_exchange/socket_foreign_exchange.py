"""
코인 정보 추상화
"""

from typing import Callable, Coroutine, Any
from common.utils.other_utils import get_symbol_collect_url
from common.core.abstract import AbstractExchangeSocketClient
from common.setting.socket_parameter import (
    binance_socket_paramater,
    kraken_socket_parameter,
    okx_socket_parameter,
    gateio_socket_parameter,
    bybit_socket_parameter,
)

from common.core.types import SubScribeFormat


class CoinExchangeSocketClient(AbstractExchangeSocketClient):
    def __init__(
        self, target: str, socket_parameter: Callable[[str], SubScribeFormat]
    ) -> None:
        self._websocket = get_symbol_collect_url(target, "socket")
        self.socket_parameter = socket_parameter

    # fmt: off
    async def get_present_websocket(self, symbol: str, req_type: str) -> None:
        from pipe.foreign.foreign_websocket_client import (
            ForeignWebsocketConnection as WCM
        )

        return await WCM().websocket_to_json(
            uri=self._websocket,
            subs_fmt=self.socket_parameter(symbol=symbol, req_type=req_type),
            symbol=symbol,
        )


class BinanceSocket(CoinExchangeSocketClient):
    def __init__(self) -> None:
        super().__init__(target="binance", socket_parameter=binance_socket_paramater)

    async def get_present_websocket(self, symbol: str) -> None:
        return await super().get_present_websocket(symbol, req_type="ticker")


class KrakenSocket(CoinExchangeSocketClient):
    def __init__(self) -> None:
        super().__init__(target="kraken", socket_parameter=kraken_socket_parameter)

    async def get_present_websocket(self, symbol: str) -> None:
        return await super().get_present_websocket(symbol, req_type="ticker")


class OKXSocket(CoinExchangeSocketClient):
    def __init__(self) -> None:
        super().__init__(target="okx", socket_parameter=okx_socket_parameter)

    async def get_present_websocket(self, symbol: str) -> None:
        return await super().get_present_websocket(symbol, req_type="tickers")


class GateIOSocket(CoinExchangeSocketClient):
    def __init__(self) -> None:
        super().__init__(target="gateio", socket_parameter=gateio_socket_parameter)

    async def get_present_websocket(self, symbol: str) -> None:
        return await super().get_present_websocket(symbol, req_type="tickers")


class ByBitSocket(CoinExchangeSocketClient):
    def __init__(self) -> None:
        super().__init__(target="bybit", socket_parameter=bybit_socket_parameter)

    async def get_present_websocket(self, symbol: str) -> None:
        return await super().get_present_websocket(symbol, req_type="tickers")