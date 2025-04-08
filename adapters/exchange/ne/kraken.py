import asyncio
import json
from typing import Any, override
import logging
from adapters.exchange.base_handler import BaseAsiaEuropeHandler
from adapters.base.event.types import EventType

logger = logging.getLogger("websocket_handler")


class KrakenWebsocketHandler(BaseAsiaEuropeHandler):
    """크라켄 거래소 웹소켓 핸들러"""

    def __init__(self):
        super().__init__()
        self.heartbeat_interval = 30  # 30초마다 핑 체크

    @override
    def _is_heartbeat(self, message: Any) -> bool:
        """크라켄 핑 메시지 확인

        Args:
            message: 검사할 메시지

        Returns:
            핑 메시지 여부
        """
        return "ping" in message or "heartbeat" in message

    @override
    async def _handle_heartbeat(self, websocket, message: Any) -> None:
        """크라켄 핑 응답 처리

        Args:
            websocket: 웹소켓 객체
            message: 핑 메시지
        """
        self.last_heartbeat_time = asyncio.get_event_loop().time()
        logger.debug(f"{self.exchange_name}: 하트비트 처리")

    @override
    async def _send_heartbeat(self, websocket) -> None:
        """크라켄 하트비트 전송

        Args:
            websocket: 웹소켓 객체
        """
        await websocket.send(json.dumps({"op": "ping"}))
        logger.debug(f"{self.exchange_name}: 연결 유지 핑 전송")

    @override
    async def _parse_message(self, message: Any) -> Any:
        """크라켄 특화 메시지 파싱

        Args:
            message: 파싱할 메시지

        Returns:
            파싱된 메시지 또는 None
        """
        # 크라켄은 핑 메시지를 보낼 수 있음
        if "ping" in message or "heartbeat" in message:
            return None  # 핑/하트비트 메시지는 처리하지 않음

        return message

    @override
    def _identify_message_type(self, message: Any) -> str:
        """메시지 타입 식별

        메시지 내용에 따라 티커 또는 오더북 타입을 식별

        Args:
            message: 분류할 메시지

        Returns:
            메시지 타입(EventType.MARKET_TICKER 또는 EventType.MARKET_ORDERBOOK)
        """
        try:
            # 이 부분은 크라켄 응답 형식에 따라 파싱하여 타입 결정
            if isinstance(message, str):
                data = json.loads(message)

                # 크라켄 응답 중 티커 관련 응답 확인
                if isinstance(data, list) and len(data) > 1:
                    channel_name = data[2] if len(data) > 2 else ""

                    if "book" in channel_name:
                        return EventType.MARKET_ORDERBOOK
                    else:
                        return EventType.MARKET_TICKER

            # 기본 값은 티커
            return EventType.MARKET_TICKER

        except Exception as e:
            logger.warning(f"{self.exchange_name}: 메시지 타입 식별 오류 - {str(e)}")
            return EventType.MARKET_TICKER  # 기본값
