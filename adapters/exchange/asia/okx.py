import asyncio
import json
from typing import Any
import logging
from core.pipeline.source import BaseWebsocketHandler

logger = logging.getLogger("websocket_handler")


class OkxWebsocketHandler(BaseWebsocketHandler):
    """OKX 거래소 웹소켓 핸들러"""

    async def _parse_message(self, message: Any) -> Any:
        """OKX 특화 메시지 파싱"""
        if isinstance(message, bytes):
            message = message.decode('utf-8')
            
        # OKX는 하트비트 메시지를 보내는 경우가 있음
        if "pong" in message or "ping" in message:
            return None  # 핑/퐁 메시지는 티커 처리하지 않음
            
        return message

    async def _prepare_subscription_message(self, params: dict[str, Any]) -> str:
        """OKX 구독 메시지 준비"""
        return json.dumps(params)

    async def _handle_message_loop(self, websocket, timeout: int) -> None:
        """OKX 메시지 수신 및 처리 루프"""
        # OKX는 핑 메시지에 퐁으로 응답해야 함
        last_pong_time = asyncio.get_event_loop().time()
        
        while True:
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=timeout)
                
                # 핑 메시지 처리
                if "ping" in message:
                    pong_message = message.replace("ping", "pong")
                    await websocket.send(pong_message)
                    logger.debug(f"{self.exchange_name}: 핑-퐁 메시지 교환")
                    last_pong_time = asyncio.get_event_loop().time()
                    continue
                
                parsed_message = await self._parse_message(message)
                if parsed_message:  # None이면 처리 무시
                    await self._process_message(parsed_message)
                    
            except asyncio.TimeoutError:
                # 일정 시간 이상 메시지 없으면 연결 상태 확인
                if asyncio.get_event_loop().time() - last_pong_time > 20:
                    # 20초 이상 퐁 메시지 없으면 하트비트 전송
                    await websocket.send(json.dumps({"op": "ping"}))
                    logger.debug(f"{self.exchange_name}: 하트비트 전송")
