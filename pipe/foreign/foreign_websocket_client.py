import json
import websockets

from pipe.foreign.foreign_rest_client import ForeignExchangeRestAPI
from common.exception import SocketRetryOnFailure
from common.core.types import SubScribeFormat, ExchangeResponseData
from common.client.common_exchange_interface import (
    WebsocketConnectionManager,
    MessageDataPreprocessing,
    CommonCoinPresentPriceWebsocket,
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
        )

    async def websocket_to_json(
        self, uri: str, subs_fmt: SubScribeFormat, symbol: str
    ) -> None:
        """말단 소켓 시작 지점"""

        @SocketRetryOnFailure(
            retries=3,
            base_delay=2,
            rest_client=ForeignExchangeRestAPI(),
            symbol=symbol,
            uri=uri,
            subs=subs_fmt,
        )
        async def connection() -> None:
            async with websockets.connect(
                uri, ping_interval=30.0, ping_timeout=60.0
            ) as websocket:
                await self.socket_param_send(websocket, subs_fmt)
                await self.handle_connection(websocket, uri)
                await self.handle_message(websocket, uri, symbol)

        await connection()


class ForeignCoinPresentPriceWebsocket(CommonCoinPresentPriceWebsocket):
    """Coin Stream"""

    def __init__(
        self,
        symbol: str,
        location: str = "foreign",
        market: str = "all",
        market_type: str = "socket",
    ) -> None:
        super().__init__(location, symbol, market, market_type)
