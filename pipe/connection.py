from common.client.websocket_interface import (
    MarketsCoinTickerPriceWebsocket,
    MarketsCoinOrderBookWebsocket,
)


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
