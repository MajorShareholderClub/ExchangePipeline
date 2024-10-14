import json
import websockets

from common.core.types import ExchangeResponseData
from common.client.market_socket.websocket_interface import (
    WebsocketConnectionManager,
    BaseMessageDataPreprocessing,
)
from protocols.connection.coin_rest_api import (
    ForeignExchangeRestAPI,
    KoreaExchangeRestAPI,
)

socket_protocol = websockets.WebSocketClientProtocol


class MessageDataPreprocessing(BaseMessageDataPreprocessing):
    def __init__(self, location: str) -> None:
        super().__init__(type_="socket", location=location)

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
            "korbit": lambda msg: msg.get("event") != "korbit:subscribe" and msg.get("data"),
        }

        # 해당 거래소에 대한 필터가 정의되어 있는지 확인
        filter_function = filters.get(market)

        if isinstance(message, dict):
            # 'arg' 키가 존재하면 삭제하고 'data'로 변경
            if "arg" in message:
                del message["arg"]
                message = message.get("data", {})  # 'data'가 없으면 빈 dict 반환
            else:
                # 필터링 적용
                if filter_function and filter_function(message):
                    return message

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

    def __init__(self, location="foreign") -> None:
        self.location = location
        super().__init__(
            target="foreign",
            folder="foreign",
            process=MessageDataPreprocessing(location=location),
            rest_client=ForeignExchangeRestAPI(),
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
