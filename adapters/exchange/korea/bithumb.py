import asyncio
import json
from typing import Any
from core.pipeline.source import BaseWebsocketHandler


class BithumbWebsocketHandler(BaseWebsocketHandler):
    """빗썸 거래소 웹소켓 핸들러"""

    async def _parse_message(self, message: Any) -> Any:
        """빗썸 특화 메시지 파싱"""
        # 빗썸 응답은 문자열이므로 그대로 반환
        return message

    async def _prepare_subscription_message(self, params: dict[str, Any]) -> str:
        """빗썸 구독 메시지 준비"""
        return json.dumps(params)

    async def _handle_message_loop(self, websocket, timeout: int) -> None:
        """빗썸 메시지 수신 및 처리 루프"""
        while True:
            message = await asyncio.wait_for(websocket.recv(), timeout=timeout)
            parsed_message = await self._parse_message(message)
            if parsed_message:  # None이면 처리 무시
                await self._process_message(parsed_message)
