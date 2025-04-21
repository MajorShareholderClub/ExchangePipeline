import asyncio
import json
from typing import Any, override
import logging
from adapters.exchange.base_handler import BaseAsiaEuropeHandler
from adapters.base.event.event_bus import EventBus

logger = logging.getLogger("websocket_handler")


class BinanceWebsocketHandler(BaseAsiaEuropeHandler):
    """바이낸스 거래소 웹소켓 핸들러"""

    def __init__(self, event_bus: EventBus, exchange_name: str) -> None:
        super().__init__(event_bus, exchange_name, region="ne")
        self.heartbeat_interval = 30  # 30초마다 핑 체크

    @override
    def _is_heartbeat(self, message: Any) -> bool:
        """바이낸스 핑 메시지 확인

        Args:
            message: 검사할 메시지

        Returns:
            핑 메시지 여부
        """
        if isinstance(message, str):
            return message == "ping" or message.startswith('{"ping"')
        return False

    @override
    async def _handle_heartbeat(self, websocket, message: Any) -> None:
        """바이낸스 핑 응답 처리

        Args:
            websocket: 웹소켓 객체
            message: 핑 메시지
        """
        await websocket.send("pong")
        logger.debug(f"{self.exchange_name}: 핑-퐁 메시지 교환")
        self.last_heartbeat_time = asyncio.get_event_loop().time()

    @override
    async def _send_heartbeat(self, websocket) -> None:
        """바이낸스 하트비트 전송

        Args:
            websocket: 웹소켓 객체
        """
        await websocket.send(json.dumps({"method": "ping"}))
        logger.debug(f"{self.exchange_name}: 하트비트 전송")

    @override
    async def _parse_message(self, message: Any) -> Any:
        """바이낸스 특화 메시지 파싱

        Args:
            message: 파싱할 메시지

        Returns:
            파싱된 메시지 또는 None
        """
        # 바이낸스 메시지 타입을 확인하여 핑 메시지 필터링
        if isinstance(message, str):
            if message == "ping" or message.startswith('{"ping"'):
                return None  # 핑 메시지는 처리하지 않음

            if "result" in message and message["result"] is None:
                return None  # 무시

        message = json.loads(message)
        return message
