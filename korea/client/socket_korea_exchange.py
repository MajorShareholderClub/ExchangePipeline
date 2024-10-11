"""
코인 정보 추상화
"""

from common.core.abstract import AbstractExchangeSocketClient
from common.setting.socket_parameter import (
    upbithumb_socket_parameter,
    coinone_socket_parameter,
    korbit_socket_parameter,
)


class CoinExchangeSocketConnection(AbstractExchangeSocketClient):
    async def get_present_websocket(self, symbol: str, socket_type: str) -> None:
        from korea.connection.korea_websocket_connect import (
            KoreaWebsocketConnection as WCM,
        )

        """소켓 출발점"""
        return await WCM().websocket_to_json(
            uri=self._websocket,
            subs_fmt=self.socket_parameter(symbol=symbol, req_type=socket_type),
            symbol=symbol,
            socket_type=socket_type,
        )


class UpbitSocket(CoinExchangeSocketConnection):
    def __init__(self) -> None:
        super().__init__(target="upbit", socket_parameter=upbithumb_socket_parameter)

    async def price_present_websocket(self, symbol: str) -> None:
        return await super().get_present_websocket(symbol, socket_type=self.ticker)

    async def orderbook_present_websocket(self, symbol: str) -> None:
        return await super().get_present_websocket(symbol, socket_type=self.orderbook)


class BithumbSocket(CoinExchangeSocketConnection):
    def __init__(self) -> None:
        super().__init__(target="bithumb", socket_parameter=upbithumb_socket_parameter)

    async def price_present_websocket(self, symbol: str) -> None:
        return await super().get_present_websocket(symbol, socket_type=self.ticker)

    async def orderbook_present_websocket(self, symbol: str) -> None:
        return await super().get_present_websocket(symbol, socket_type=self.orderbook)


class CoinoneSocket(CoinExchangeSocketConnection):
    def __init__(self) -> None:
        super().__init__(target="coinone", socket_parameter=coinone_socket_parameter)

    async def price_present_websocket(self, symbol: str) -> None:
        return await super().get_present_websocket(symbol, socket_type=self.ticker)

    async def orderbook_present_websocket(self, symbol: str) -> None:
        return await super().get_present_websocket(symbol, socket_type=self.orderbook)


class KorbitSocket(CoinExchangeSocketConnection):
    def __init__(self) -> None:
        super().__init__(target="korbit", socket_parameter=korbit_socket_parameter)

    async def price_present_websocket(self, symbol: str) -> None:
        return await super().get_present_websocket(symbol, socket_type=self.ticker)

    async def orderbook_present_websocket(self, symbol: str) -> None:
        return await super().get_present_websocket(symbol, socket_type=self.orderbook)
