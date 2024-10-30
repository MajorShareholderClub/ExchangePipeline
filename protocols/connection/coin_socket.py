import websockets

from common.client.market_socket.websocket_interface import (
    WebsocketConnectionManager,
)
from protocols.connection.coin_rest_api import (
    AsiaxchangeRestAPI,
    KoreaExchangeRestAPI,
    NEExchangeRestAPI,
)

socket_protocol = websockets.WebSocketClientProtocol


class AsiaWebsocketConnection(WebsocketConnectionManager):
    """웹소켓 승인 전송 로직"""

    def __init__(self, location="asia") -> None:
        self.location = location
        super().__init__(
            location="asia",
            folder="asia",
            rest_client=AsiaxchangeRestAPI(),
        )


class NEWebsocketConnection(WebsocketConnectionManager):
    """웹소켓 승인 전송 로직"""

    def __init__(self, location="ne") -> None:
        self.location = location
        super().__init__(
            location="ne",
            folder="ne",
            rest_client=NEExchangeRestAPI(),
        )


class KoreaWebsocketConnection(WebsocketConnectionManager):
    """웹소켓 승인 전송 로직"""

    def __init__(self, location="korea") -> None:
        super().__init__(
            location="korea",
            folder="korea",
            rest_client=KoreaExchangeRestAPI(),
        )
