import json
import websockets

from pipe.korea.korea_rest_client import KoreaExchangeRestAPI
from common.core.types import ExchangeResponseData
from common.client.market_socket.websocket_interface import (
    WebsocketConnectionManager,
    MessageDataPreprocessing,
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
            "korbit": lambda msg: msg.get("event") != 'korbit:subscribe' and msg.get("data")
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
        await super().put_message_to_logging(uri, symbol, process)


class KoreaWebsocketConnection(WebsocketConnectionManager):
    """웹소켓 승인 전송 로직"""

    def __init__(self) -> None:
        super().__init__(
            target="korea",
            folder="korea",
            process=KoreaMessageDataPreprocessing(),
            rest_client=KoreaExchangeRestAPI(),
        )
