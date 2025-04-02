import asyncio
import json
from typing import Any
import logging
from core.pipeline.source import BaseWebsocketHandler

logger = logging.getLogger("websocket_handler")


class BybitWebsocketHandler(BaseWebsocketHandler):
    """바이비트 거래소 웹소켓 핸들러"""

    async def _parse_message(self, message: Any) -> Any:
        """바이비트 특화 메시지 파싱"""
        if isinstance(message, bytes):
            message = message.decode('utf-8')
            
        # 바이비트는 특정 타입의 메시지를 필터링
        json_msg = json.loads(message) if isinstance(message, str) else message
        if "op" in json_msg and json_msg["op"] == "ping":
            return None  # 핑 메시지는 처리하지 않음
            
        return message

    async def _prepare_subscription_message(self, params: dict[str, Any]) -> str:
        """바이비트 구독 메시지 준비"""
        return json.dumps(params)

    async def _handle_message_loop(self, websocket, timeout: int) -> None:
        """바이비트 메시지 수신 및 처리 루프"""
        # 바이비트는 주기적인 핑-퐁 필요
        last_pong_time = asyncio.get_event_loop().time()
        
        while True:
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=timeout)
                
                # JSON 파싱
                json_msg = json.loads(message) if isinstance(message, str) else message
                
                # 핑 메시지 처리
                if isinstance(json_msg, dict) and "op" in json_msg and json_msg["op"] == "ping":
                    pong_message = json.dumps({"op": "pong", "ts": json_msg.get("ts", int(asyncio.get_event_loop().time() * 1000))})
                    await websocket.send(pong_message)
                    logger.debug(f"{self.exchange_name}: 핑-퐁 메시지 교환")
                    last_pong_time = asyncio.get_event_loop().time()
                    continue
                
                parsed_message = await self._parse_message(message)
                if parsed_message:  # None이면 처리 무시
                    await self._process_message(parsed_message)
                    
            except asyncio.TimeoutError:
                # 일정 시간 이상 메시지 없으면 연결 상태 확인
                if asyncio.get_event_loop().time() - last_pong_time > 25:
                    # 25초 이상 퐁 메시지 없으면 하트비트 전송
                    await websocket.send(json.dumps({"op": "ping", "ts": int(asyncio.get_event_loop().time() * 1000)}))
                    logger.debug(f"{self.exchange_name}: 하트비트 전송")
