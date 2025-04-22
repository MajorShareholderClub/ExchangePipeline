import asyncio
import json
from typing import Any, override
import logging
from adapters.exchange.base_handler import BaseAsiaEuropeHandler
from adapters.exchange.utils import update_dict
from adapters.base.event.event_bus import EventBus
from common.exceptions import AsyncException

logger = logging.getLogger("websocket_handler")


class BybitWebsocketHandler(BaseAsiaEuropeHandler):
    """바이비트 거래소 웹소켓 핸들러"""

    def __init__(
        self, event_bus: EventBus, exchange_name: str, region: str, request_type: str
    ) -> None:
        super().__init__(event_bus, exchange_name, region, request_type)
        self.heartbeat_interval = 20  # 20초마다 핑 체크

    @override
    def _is_heartbeat(self, message: Any) -> bool:
        """바이비트 핑 메시지 확인

        Args:
            message: 검사할 메시지

        Returns:
            핑 메시지 여부
        """
        if isinstance(message, str):
            json_msg = json.loads(message)
            return "op" in json_msg and json_msg["op"] == "ping"
        return False

    @override
    async def _handle_heartbeat(self, websocket, message: Any) -> None:
        """바이비트 핑 응답 처리

        Args:
            websocket: 웹소켓 객체
            message: 핑 메시지
        """
        try:
            json_msg = json.loads(message) if isinstance(message, str) else message
            time = int(asyncio.get_event_loop().time() * 1000)
            pong_message = json.dumps(
                {
                    "op": "pong",
                    "ts": json_msg.get("ts", time),
                }
            )
            await websocket.send(pong_message)
            logger.debug(f"{self.exchange_name}: 핑-퐁 메시지 교환")
            self.last_heartbeat_time = asyncio.get_event_loop().time()
        except AsyncException as e:
            logger.warning(f"{self.exchange_name}: 핑 응답 처리 중 오류 - {str(e)}")

    @override
    async def _send_heartbeat(self, websocket) -> None:
        """바이비트 하트비트 전송

        Args:
            websocket: 웹소켓 객체
        """
        time = int(asyncio.get_event_loop().time() * 1000)
        await websocket.send(
            json.dumps(
                {
                    "op": "ping",
                    "ts": time,
                }
            )
        )
        logger.debug(f"{self.exchange_name}: 하트비트 전송")

    @override
    async def _parse_message(self, message: dict) -> dict:
        """바이비트 특화 메시지 파싱

        Args:
            message: 파싱할 메시지

        Returns:
            파싱된 메시지 또는 None
        """

        if isinstance(message, str):
            json_msg: dict = json.loads(message)

            if "op" in json_msg and json_msg["op"] == "ping":
                return None  # 핑 메시지는 처리하지 않음

            if json_msg.get("op") == "subscribe":
                return None  # 구독 메시지는 처리하지 않음

        message: dict = update_dict(json_msg, "data")
        return message
