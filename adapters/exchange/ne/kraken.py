import asyncio
import json
from typing import Any, override
import logging
from adapters.exchange.base_handler import BaseAsiaEuropeHandler
from adapters.exchange.utils import update_dict
from adapters.base.event.event_bus import EventBus

logger = logging.getLogger("websocket_handler")


class KrakenWebsocketHandler(BaseAsiaEuropeHandler):
    """크라켄 거래소 웹소켓 핸들러"""

    def __init__(
        self, event_bus: EventBus, exchange_name: str, region: str, request_type: str
    ) -> None:
        super().__init__(event_bus, exchange_name, region, request_type)
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

        json_msg: dict = json.loads(message)
        if json_msg.get("channel") == "status":
            return None  # 상태 메시지는 처리하지 않음
        if json_msg.get("method") == "subscribe":
            return None  # 구독 메시지는 처리하지 않음

        message: dict = update_dict(json_msg, "data")
        return message
