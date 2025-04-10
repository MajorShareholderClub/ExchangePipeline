import asyncio
import json
from typing import Any, override
import logging
from adapters.exchange.base_handler import BaseAsiaEuropeHandler
from adapters.base.event.event_bus import EventBus
from common.exceptions import AsyncException

logger = logging.getLogger("websocket_handler")


class GateioWebsocketHandler(BaseAsiaEuropeHandler):
    """Gate.io 거래소 웹소켓 핸들러"""

    def __init__(self, event_bus: EventBus, exchange_name: str) -> None:
        super().__init__(event_bus, exchange_name)
        self.heartbeat_interval = 20  # 20초마다 핑 전송

    @override
    def _is_heartbeat(self, message: Any) -> bool:
        """Gate.io의 하트비트 메시지 확인

        Args:
            message: 검사할 메시지

        Returns:
            하트비트 메시지 여부
        """
        # Gate.io는 서버에서 하트비트를 받지 않고 클라이언트에서 보내는 방식을 사용함
        try:
            json_msg = json.loads(message) if isinstance(message, str) else message
            return "method" in json_msg and json_msg["method"] == "ping"
        except Exception:
            return False

    @override
    async def _handle_heartbeat(self, websocket, message: Any) -> None:
        """Gate.io의 하트비트 응답 처리

        Args:
            websocket: 웹소켓 객체
            message: 하트비트 메시지
        """
        # Gate.io는 핑에 대한 특별한 응답이 필요 없음
        self.last_heartbeat_time = asyncio.get_event_loop().time()

    @override
    async def _send_heartbeat(self, websocket) -> None:
        """Gate.io의 하트비트 전송

        Args:
            websocket: 웹소켓 객체
        """
        time = int(asyncio.get_event_loop().time() * 1000)
        ping_message = json.dumps({"method": "ping", "params": [], "id": time})
        await websocket.send(ping_message)
        logger.debug(f"{self.exchange_name}: 하트비트 전송")

    @override
    async def _parse_message(self, message: Any) -> Any:
        """Gate.io 특화 메시지 파싱"""
        if isinstance(message, bytes):
            message = message.decode("utf-8")

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

    @override
    async def _handle_message_loop(self, websocket, timeout: int) -> None:
        """Gate.io 메시지 수신 및 처리 루프"""
        # Gate.io는 주기적인 핑 메시지 필요
        self.last_heartbeat_time = asyncio.get_event_loop().time()  # 초기화

        while True:
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=timeout)

                # 주기적 핑 메시지 전송
                current_time = asyncio.get_event_loop().time()
                if current_time - self.last_heartbeat_time > self.heartbeat_interval:
                    await self._send_heartbeat(websocket)
                    self.last_heartbeat_time = current_time

                # 하트비트 메시지 처리
                if self._is_heartbeat(message):
                    await self._handle_heartbeat(websocket, message)
                    continue

                # 응답 처리
                parsed_message = await self._parse_message(message)
                if parsed_message:  # None이면 처리 무시
                    await self._process_message(parsed_message)

            except AsyncException:
                # 타임아웃 발생 시 핑 및 재연결 시도
                await self._send_heartbeat(websocket)
                self.last_heartbeat_time = asyncio.get_event_loop().time()
