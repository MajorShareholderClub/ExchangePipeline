import websockets

from common.core.types import ResponseData
from common.utils.other_util import market_name_extract
from common.client.market_socket.websocket_interface import (
    WebsocketConnectionManager,
    BaseMessageDataPreprocessing,
)
from protocols.connection.coin_rest_api import (
    AsiaxchangeRestAPI,
    KoreaExchangeRestAPI,
    NEExchangeRestAPI,
)

socket_protocol = websockets.WebSocketClientProtocol


class MessageDataPreprocessing(BaseMessageDataPreprocessing):
    def __init__(self, location: str) -> None:
        super().__init__(type_="socket", location=location)
        self.connect = []

    async def put_message_to_logging(
        self, message: ResponseData, uri: str, symbol: str
    ) -> None:
        market: str = market_name_extract(uri=uri)
        await super().put_message_to_logging(market, symbol, message=message)


class AsiaWebsocketConnection(WebsocketConnectionManager):
    """웹소켓 승인 전송 로직"""

    def __init__(self, location="asia") -> None:
        self.location = location
        super().__init__(
            target="asia",
            folder="asia",
            process=MessageDataPreprocessing(location=location),
            rest_client=AsiaxchangeRestAPI(),
        )


class NEWebsocketConnection(WebsocketConnectionManager):
    """웹소켓 승인 전송 로직"""

    def __init__(self, location="ne") -> None:
        self.location = location
        super().__init__(
            target="ne",
            folder="ne",
            process=MessageDataPreprocessing(location=location),
            rest_client=NEExchangeRestAPI(),
        )


class KoreaWebsocketConnection(WebsocketConnectionManager):
    """웹소켓 승인 전송 로직"""

    def __init__(self, location="korea") -> None:
        super().__init__(
            target="korea",
            folder="korea",
            process=MessageDataPreprocessing(location=location),
            rest_client=KoreaExchangeRestAPI(),
        )
