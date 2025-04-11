import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, override

from adapters.base.event.event_bus import EventBus
from common.exceptions import AsyncException
from common.setting.config.yml_config import get_ticker_format
from core.pipeline.source import BaseWebsocketHandler

logger = logging.getLogger("websocket_handler_testting")
KoreaResponseData = dict[str, int | float]


class BaseAsiaEuropeHandler(BaseWebsocketHandler, ABC):
    """아시아 및 유럽 지역 거래소를 위한 공통 베이스 핸들러

    공통 메시지 루프 및 핑-퐁 메커니즘을 제공하여 코드 중복을 최소화합니다.
    """

    def __init__(self, event_bus: EventBus, exchange_name: str) -> None:
        super().__init__(event_bus, exchange_name)
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


class BaseKoreaWebsocketHandler(BaseWebsocketHandler, ABC):
    """한국 거래소 웹소켓 핸들러"""

    async def process_ticker_message(
        self, message: dict, ticker_format: list[str]
    ) -> KoreaResponseData:
        """
        티커 메시지 처리 함수.

        전제:
        - 일부 필드는 message 최상위에 존재하고,
        - 나머지는 message["data"] 내부에 존재합니다.

        Args:
            message: 티커 메시지 (예: {"timestamp": ..., "data": {...}})
            ticker_format: 추출할 필드 목록 (예: ["timestamp", "open", "close", "volume"])

        Returns:
            dict[str, int | float]: ticker_format에 해당하는 필드만 포함한 결과 dict
        """
        if isinstance(message, dict):
            coinone_type: str = message.get("response_type", "")
            if coinone_type in ["CONNECTED", "SUBSCRIBED"]:
                return None

        data_sub: dict = message.get("data", {})  # "data"가 없다면 빈 dict 사용

        return {
            field: (
                message.get(field, None)
                if field in message
                else data_sub.get(field, None)
            )
            for field in ticker_format
        }

    async def _preprocess_message(self, message: Any, ticker_format: list[str]) -> Any:
        """특화 메시지 처리"""
        return await self.process_ticker_message(message, ticker_format)

    @override
    async def _handle_message_loop(self, websocket, timeout: int) -> None:
        """메시지 수신 및 처리 루프"""
        while True:
            message = await asyncio.wait_for(websocket.recv(), timeout=timeout)
            ticker_format: list[str] | None = get_ticker_format(self.exchange_name)
            parsed_message = await self._parse_message(message)

            p_data = await self._preprocess_message(parsed_message, ticker_format)
            if p_data:
                await self._process_message(p_data)
