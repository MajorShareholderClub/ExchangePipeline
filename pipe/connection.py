from common.client.market_socket.async_socket_client import (
    PriceWebSocketClient,
    OrderBookWebSocketClient,
)
from config.yml_param_load import SocketMarketLoader


class CoinPresentPriceWebsocket(PriceWebSocketClient):
    def __init__(
        self,
        symbol: str,
        location: str,
        market: str = "all",
    ) -> None:
        self.market_env = SocketMarketLoader(location=location).process_market_info()
        super().__init__(symbol=symbol, market=market, market_env=self.market_env)


class CoinOrderBookWebsocket(OrderBookWebSocketClient):
    def __init__(
        self,
        symbol: str,
        location: str,
        market: str = "all",
    ) -> None:
        self.market_env = SocketMarketLoader(location=location).process_market_info()
        super().__init__(symbol=symbol, market=market, market_env=self.market_env)
