import asyncio
import json
from typing import Any
import logging
from core.pipeline.source import BaseWebsocketHandler

logger = logging.getLogger("websocket_handler")


class GateioWebsocketHandler(BaseWebsocketHandler):
    """Gate.io 거래소 웹소켓 핸들러"""

    async def _parse_message(self, message: Any) -> Any:
        """Gate.io 특화 메시지 파싱"""
        if isinstance(message, bytes):
            message = message.decode('utf-8')
            
        # Gate.io는 필터링이 필요한 메시지 처리
        try:
            json_msg = json.loads(message)
            # 시스템 메시지 처리 (예: 인증, 결과 메시지 등)
            if "id" in json_msg and "error" in json_msg:
                if json_msg["error"] is None:
                    return None  # 성공 응답은 무시
                logger.error(f"Gate.io API 오류: {json_msg['error']}")
                return None
            
            # 핑 응답 필터링
            if "method" in json_msg and json_msg["method"] == "ping":
                return None
            
            return message
        except json.JSONDecodeError:
            # JSON이 아닌 메시지는 그대로 반환
            return message

    async def _prepare_subscription_message(self, params: dict[str, Any]) -> str:
        """Gate.io 구독 메시지 준비"""
        return json.dumps(params)

    async def _handle_message_loop(self, websocket, timeout: int) -> None:
        """Gate.io 메시지 수신 및 처리 루프"""
        # Gate.io는 주기적인 핑 메시지 필요
        last_ping_time = asyncio.get_event_loop().time()
        
        while True:
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=timeout)
                
                # 주기적 핑 메시지 전송
                current_time = asyncio.get_event_loop().time()
                if current_time - last_ping_time > 20:  # 20초마다 핑 전송
                    ping_message = json.dumps({"method": "ping", "params": [], "id": int(current_time * 1000)})
                    await websocket.send(ping_message)
                    logger.debug(f"{self.exchange_name}: 핑 메시지 전송")
                    last_ping_time = current_time
                
                # 응답 처리
                parsed_message = await self._parse_message(message)
                if parsed_message:  # None이면 처리 무시
                    await self._process_message(parsed_message)
                    
            except asyncio.TimeoutError:
                # 타임아웃 발생 시 핑 및 재연결 시도
                ping_message = json.dumps({"method": "ping", "params": [], "id": int(asyncio.get_event_loop().time() * 1000)})
                await websocket.send(ping_message)
                logger.debug(f"{self.exchange_name}: 연결 유지 핑 전송")