"""
코인 정보 추상화
"""

from common.core.abstract import AbstractExchangeSocketClient
from common.setting.socket_parameter import (
    okx_socket_parameter,
    gateio_socket_parameter,
    bybit_socket_parameter,
)


class CoinExchangeSocketClient(AbstractExchangeSocketClient):
    async def get_present_websocket(
        self, symbol: str, req_type: str, socket_type: str
    ) -> None:
        from protocols.connection.coin_socket import (
            ForeignWebsocketConnection as WCM,
        )

        """소켓 출발점"""
        return await WCM().websocket_to_json(
            uri=self._websocket,
            subs_fmt=self.socket_parameter(symbol=symbol, req_type=req_type),
            symbol=symbol,
            socket_type=socket_type,
        )


class GateIOSocket(CoinExchangeSocketClient):
    def __init__(self) -> None:
        super().__init__(
            target="gateio", location="asia", socket_parameter=gateio_socket_parameter
        )

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
        super().__init__(
            target="okx", location="asia", socket_parameter=okx_socket_parameter
        )

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
        super().__init__(
            target="bybit", location="asia", socket_parameter=bybit_socket_parameter
        )

    async def price_present_websocket(self, symbol: str) -> None:
        return await super().get_present_websocket(
            symbol, req_type="tickers", socket_type=self.ticker
        )

    async def orderbook_present_websocket(self, symbol: str) -> None:
        return await super().get_present_websocket(
            symbol, req_type="orderbook", socket_type=self.orderbook
        )
