import asyncio
from typing import Any, override
import logging
from core.pipeline.source import BaseWebsocketHandler
from adapters.base.event.types import AsyncException
from abc import ABC, abstractmethod

logger = logging.getLogger("websocket_handler")


class BaseAsiaEuropeHandler(BaseWebsocketHandler, ABC):
    """아시아 및 유럽 지역 거래소를 위한 공통 베이스 핸들러

    공통 메시지 루프 및 핑-퐁 메커니즘을 제공하여 코드 중복을 최소화합니다.
    """

    def __init__(self):
        super().__init__()
        self.last_heartbeat_time = 0  # 최근 하트비트 시간
        self.heartbeat_interval = 30  # 기본 30초 간격

    @abstractmethod
    def _is_heartbeat(self, message: Any) -> bool:
        """하트비트(핑/퐁) 메시지인지 확인

        각 거래소별로 오버라이드해야 함

        Args:
            message: 검사할 메시지

        Returns:
            하트비트 메시지 여부
        """
        raise NotImplementedError()

    @abstractmethod
    async def _handle_heartbeat(self, websocket, message: Any) -> None:
        """하트비트 메시지 처리

        각 거래소별로 오버라이드해야 함

        Args:
            websocket: 웹소켓 객체
            message: 하트비트 메시지
        """
        raise NotImplementedError()

    @abstractmethod
    async def _send_heartbeat(self, websocket) -> None:
        """하트비트 메시지 전송

        각 거래소별로 오버라이드해야 함

        Args:
            websocket: 웹소켓 객체
        """
        raise NotImplementedError()

    @override
    async def _handle_message_loop(self, websocket, timeout: int) -> None:
        """메시지 수신 및 처리 공통 루프

        Args:
            websocket: 웹소켓 객체
            timeout: 타임아웃 시간(초)
        """
        self.last_heartbeat_time = asyncio.get_event_loop().time()  # 초기화

        while True:
            try:
                # 1. 메시지 수신
                message = await asyncio.wait_for(websocket.recv(), timeout=timeout)

                # 2. 하트비트 메시지 처리
                if self._is_heartbeat(message):
                    await self._handle_heartbeat(websocket, message)
                    continue

                # 3. 메시지 파싱
                parsed_message = await self._parse_message(message)
                if parsed_message:  # None이면 처리 무시
                    # 4. 메시지 처리
                    await self._process_message(parsed_message)

            except AsyncException:
                # 타임아웃 발생 - 하트비트 필요 확인
                current_time = asyncio.get_event_loop().time()
                if current_time - self.last_heartbeat_time > self.heartbeat_interval:
                    # 설정된 시간 이상 하트비트 없으면 발송
                    await self._send_heartbeat(websocket)
                    logger.debug(f"{self.exchange_name}: 하트비트 전송")
                    self.last_heartbeat_time = current_time


class BaseKoreaWebsocketHandler(BaseWebsocketHandler):
    """한국 거래소 웹소켓 핸들러"""

    @override
    async def _handle_message_loop(self, websocket, timeout: int) -> None:
        """메시지 수신 및 처리 루프"""
        while True:
            message = await asyncio.wait_for(websocket.recv(), timeout=timeout)
            parsed_message = await self._parse_message(message)
            if parsed_message:
                await self._process_message(parsed_message)
