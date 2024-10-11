"""
코인 정보 추상화
"""

from common.client.market_socket.async_socket_client import CoinExchangeSocketClient
from common.setting.socket_parameter import (
    upbithumb_socket_parameter,
    coinone_socket_parameter,
    korbit_socket_parameter,
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
