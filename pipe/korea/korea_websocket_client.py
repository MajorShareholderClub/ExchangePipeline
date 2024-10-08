import json
import websockets

from pipe.korea.korea_rest_client import KoreaExchangeRestAPI
from common.exception import SocketRetryOnFailure
from common.core.types import SubScribeFormat, ExchangeResponseData
from pipe.common.socket_common import (
    WebsocketConnectionManager,
    MessageDataPreprocessing,
    CommonCoinPresentPriceWebsocket,
)

socket_protocol = websockets.WebSocketClientProtocol


class KoreaMessageDataPreprocessing(MessageDataPreprocessing):
    def __init__(self) -> None:
        super().__init__(type_="socket", location="korea")

    def process_exchange(
        self, market: str, message: ExchangeResponseData
    ) -> ExchangeResponseData:
        """message 필터링
        Args:
            market: 거래소
            message: 데이터
        Returns:
            dict: connection 거친 후 본 데이터
        """
        # 거래소별 필터링 규칙 정의
        # fmt: off
        filters = {
            "coinone": lambda msg: msg.get("response_type") != "SUBSCRIBED" and msg.get("data"),
        }
        # 해당 거래소에 대한 필터가 정의되어 있는지 확인
        filter_function = filters.get(market)
        if filter_function:
            result = filters[market](message)
            if result:
                return result
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
        print(process)
        await super().put_message_to_logging(uri, symbol, process)


class KoreaWebsocketConnection(WebsocketConnectionManager):
    """웹소켓 승인 전송 로직"""

    def __init__(self) -> None:
        super().__init__(
            target="korea",
            folder="korea",
            process=KoreaMessageDataPreprocessing(),
        )

    async def websocket_to_json(
        self, uri: str, subs_fmt: SubScribeFormat, symbol: str
    ) -> None:
        """말단 소켓 시작 지점"""

        @SocketRetryOnFailure(
            retries=3,
            base_delay=2,
            rest_client=KoreaExchangeRestAPI(),
            symbol=symbol,
            uri=uri,
            subs=subs_fmt,
        )
        async def connection():
            async with websockets.connect(
                uri, ping_interval=30.0, ping_timeout=60.0
            ) as websocket:
                await self.socket_param_send(websocket, subs_fmt)
                await self.handle_connection(websocket, uri)
                await self.handle_message(websocket, uri, symbol)

        await connection()


class KoreaCoinPresentPriceWebsocket(CommonCoinPresentPriceWebsocket):
    """Coin Stream"""

    def __init__(
        self,
        symbol: str,
        location: str = "korea",
        market: str = "all",
        market_type: str = "socket",
    ) -> None:
        super().__init__(location, symbol, market, market_type)
