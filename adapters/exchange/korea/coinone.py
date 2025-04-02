import asyncio
import json
from typing import Any
from core.pipeline.source import BaseWebsocketHandler


class CoinoneWebsocketHandler(BaseWebsocketHandler):
    """코인원 거래소 웹소켓 핸들러"""

    async def _parse_message(self, message: Any) -> Any:
        """코인원 특화 메시지 파싱"""
        if isinstance(message, bytes):
            message = message.decode("utf-8")
        return message

    async def _prepare_subscription_message(self, params: dict[str, Any]) -> str:
        """코인원 구독 메시지 준비"""
        return json.dumps(params)

    async def _handle_message_loop(self, websocket, timeout: int) -> None:
        """코인원 메시지 수신 및 처리 루프"""
        while True:
            message = await asyncio.wait_for(websocket.recv(), timeout=timeout)
            parsed_message = await self._parse_message(message)
            if parsed_message:
                await self._process_message(parsed_message)
