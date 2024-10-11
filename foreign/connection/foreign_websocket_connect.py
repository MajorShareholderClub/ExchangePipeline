import json
import websockets

from foreign.connection.foreign_rest_connect import ForeignExchangeRestAPI
from common.core.types import ExchangeResponseData
from common.client.market_socket.websocket_interface import (
    WebsocketConnectionManager,
    MessageDataPreprocessing,
)


socket_protocol = websockets.WebSocketClientProtocol


class ForeignMessageDataPreprocessing(MessageDataPreprocessing):
    def __init__(self) -> None:
        super().__init__(type_="socket", location="foreign")

    def process_exchange(
        self, market: str, message: ExchangeResponseData
    ) -> ExchangeResponseData:
        if isinstance(message, dict):
            if "arg" in list(message.keys()):
                del message["arg"]
                message = message["data"]
            else:
                message = message

        return message

    async def put_message_to_logging(
        self,
        message: ExchangeResponseData,
        uri: str,
        symbol: str,
        market: str,
    ) -> None:
        process: ExchangeResponseData = self.process_exchange(
            market=market, message=json.loads(message)
        )
        await super().put_message_to_logging(uri, symbol, process)


class ForeignWebsocketConnection(WebsocketConnectionManager):
    """웹소켓 승인 전송 로직"""

    def __init__(self) -> None:
        super().__init__(
            target="foreign",
            folder="foreign",
            process=ForeignMessageDataPreprocessing(),
            rest_client=ForeignExchangeRestAPI(),
        )
