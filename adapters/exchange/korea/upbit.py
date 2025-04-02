import asyncio
import json
from typing import Any
from core.pipeline.source import BaseWebsocketHandler


class UpbitWebsocketHandler(BaseWebsocketHandler):
    """업비트 거래소 웹소켓 핸들러"""

    async def _parse_message(self, message: Any) -> Any:
        """업비트 특화 메시지 파싱"""
        if isinstance(message, bytes):
            message = message.decode('utf-8')
        return message

    async def _prepare_subscription_message(self, params: dict[str, Any]) -> str:
        """업비트 구독 메시지 준비"""
        return json.dumps(params)

    async def _handle_message_loop(self, websocket, timeout: int) -> None:
        """업비트 메시지 수신 및 처리 루프"""
        # 업비트 특화 처리 로직
        while True:
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=timeout)
                parsed_message = await self._parse_message(message)
                if parsed_message:  # None이면 처리 무시
                    await self._process_message(parsed_message)
            except asyncio.TimeoutError:
                # 업비트는 타임아웃 발생 시 핑 메시지 전송
                await websocket.send(json.dumps({"type": "ping"}))
