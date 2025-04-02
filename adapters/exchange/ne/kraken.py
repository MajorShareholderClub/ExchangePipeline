import asyncio
import json
from typing import Any
import logging
from core.pipeline.source import BaseWebsocketHandler

logger = logging.getLogger("websocket_handler")


class KrakenWebsocketHandler(BaseWebsocketHandler):
    """크라켄 거래소 웹소켓 핸들러"""

    async def _parse_message(self, message: Any) -> Any:
        """크라켄 특화 메시지 파싱"""
        if isinstance(message, bytes):
            message = message.decode("utf-8")

        # 크라켄은 핑 메시지를 보낼 수 있음
        if "ping" in message or "heartbeat" in message:
            return None  # 핑/하트비트 메시지는 처리하지 않음

        return message

    async def _prepare_subscription_message(self, params: dict[str, Any]) -> str:
        """크라켄 구독 메시지 준비"""
        return json.dumps(params)

    async def _handle_message_loop(self, websocket, timeout: int) -> None:
        """크라켄 메시지 수신 및 처리 루프"""
        # 크라켄은 하트비트가 없을 수 있으므로 직접 보내야 함
        last_ping_time = asyncio.get_event_loop().time()

        while True:
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=timeout)

                # 지정된 시간마다 핑 메시지 전송
                current_time = asyncio.get_event_loop().time()
                if current_time - last_ping_time > 30:  # 30초마다 핑 전송
                    await websocket.send(json.dumps({"op": "ping"}))
                    logger.debug(f"{self.exchange_name}: 하트비트 전송")
                    last_ping_time = current_time

                # 하트비트 메시지 처리
                if "heartbeat" in message:
                    continue

                parsed_message = await self._parse_message(message)
                if parsed_message:  # None이면 처리 무시
                    await self._process_message(parsed_message)

            except asyncio.TimeoutError:
                # 타임아웃 발생 시 핑 전송
                await websocket.send(json.dumps({"op": "ping"}))
                logger.debug(f"{self.exchange_name}: 연결 유지 핑 전송")
