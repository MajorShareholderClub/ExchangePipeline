import websockets
from common.client.market_socket.async_socket_client import (
    create_price_websocket_client,
    create_orderbook_websocket_client,
    WebSocketClient,
)
from common.client.market_socket.websocket_interface import WebsocketConnectionManager
from protocols.connection.coin_rest_api import (
    AsiaxchangeRestAPI,
    KoreaExchangeRestAPI,
    NEExchangeRestAPI,
)
from config.yml_param_load import SocketMarketLoader

socket_protocol = websockets.WebSocketClientProtocol


# 지역별 웹소켓 연결 관리자
class RegionWebsocketConnection:
    """지역별 웹소켓 연결 관리"""

    def __init__(self, location: str, rest_client) -> None:
        self.location = location
        self.connection_manager = WebsocketConnectionManager(
            location=location,
            folder=location,
            rest_client=rest_client,
        )
        self.market_env = SocketMarketLoader(location=location).process_market_info()

    def create_price_client(self, symbol: str, market: str = "all") -> WebSocketClient:
        """가격 웹소켓 클라이언트 생성"""
        return create_price_websocket_client(
            symbol=symbol,
            market_env=self.market_env,
            market=market,
        )

    def create_orderbook_client(
        self, symbol: str, market: str = "all"
    ) -> WebSocketClient:
        """호가창 웹소켓 클라이언트 생성"""
        return create_orderbook_websocket_client(
            symbol=symbol,
            market_env=self.market_env,
            market=market,
        )


# 지역별 구체적인 구현
class AsiaWebsocketConnection(RegionWebsocketConnection):
    """아시아 지역 웹소켓 연결"""

    def __init__(self) -> None:
        super().__init__(location="asia", rest_client=AsiaxchangeRestAPI())


class NEWebsocketConnection(RegionWebsocketConnection):
    """북미/유럽 지역 웹소켓 연결"""

    def __init__(self) -> None:
        super().__init__(location="ne", rest_client=NEExchangeRestAPI())


class KoreaWebsocketConnection(RegionWebsocketConnection):
    """한국 지역 웹소켓 연결"""

    def __init__(self) -> None:
        super().__init__(location="korea", rest_client=KoreaExchangeRestAPI())
