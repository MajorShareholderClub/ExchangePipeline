from typing import Callable

from common.client.market_socket.async_socket_client import BaseSettingWebsocket


class MarketsCoinTickerPriceWebsocket(BaseSettingWebsocket):
    """티커 웹소켓"""

    def get_websocket_method(self, api: Callable) -> Callable:
        return api.price_present_websocket


class MarketsCoinOrderBookWebsocket(BaseSettingWebsocket):
    """오더북 웹소켓"""

    def get_websocket_method(self, api: Callable) -> Callable:
        return api.orderbook_present_websocket


class CoinPresentPriceWebsocket(MarketsCoinTickerPriceWebsocket):
    def __init__(
        self,
        symbol: str,
        location: str,
        market: str = "all",
    ) -> None:
        super().__init__(location, symbol, market)


class CoinOrderBookWebsocket(MarketsCoinOrderBookWebsocket):
    def __init__(
        self,
        symbol: str,
        location: str,
        market: str = "all",
    ) -> None:
        super().__init__(location, symbol, market)
