import asyncio
import json
import time
from websockets import connect
from abc import ABC, abstractmethod
from typing import Any, override, Callable, Awaitable


from adapters.base.event.event_bus import EventBus
from adapters.exchange.utils import update_dict
from common.exceptions import AsyncException
from common.setting.config.yml_config import ticker_config
from core.pipeline.source import BaseWebsocketHandler


TickerResponseData = dict[str, int | float]
OrderbookResponseData = dict[str, list[str, int]]
AsyncTradeType = Awaitable[TickerResponseData | OrderbookResponseData | None]
MessageHandler = dict[str, Callable[[dict[str, Any]], AsyncTradeType]]


class BaseAsiaEuropeHandler(BaseWebsocketHandler, ABC):
    """아시아 및 유럽 지역 거래소를 위한 공통 베이스 핸들러

    공통 메시지 루프 및 핑-퐁 메커니즘을 제공하여 코드 중복을 최소화합니다.
    """

    def __init__(
        self,
        event_bus: EventBus,
        exchange_name: str,
        region: str,
        request_type: str,
    ) -> None:
        super().__init__(
            event_bus=event_bus,
            exchange_name=exchange_name,
            region=region,
            request_type=request_type,
        )
        self.last_heartbeat_time = 0  # 최근 하트비트 시간
        self.heartbeat_interval = 30  # 기본 30초 간격

    @abstractmethod
    async def _parse_message(self, message: Any) -> TickerResponseData:
        """특화 메시지 파싱"""
        raise NotImplementedError()

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
    async def _handle_heartbeat(self, websocket: connect, message: Any) -> None:
        """하트비트 메시지 처리

        각 거래소별로 오버라이드해야 함

        Args:
            websocket: 웹소켓 객체
            message: 하트비트 메시지
        """
        raise NotImplementedError()

    @abstractmethod
    async def _send_heartbeat(self, websocket: connect) -> None:
        """하트비트 메시지 전송

        각 거래소별로 오버라이드해야 함

        Args:
            websocket: 웹소켓 객체
        """
        raise NotImplementedError()

    async def _preprocess_message(self, message: dict) -> TickerResponseData:
        """메시지 처리"""
        ticker_format: list[str] = ticker_config(self.exchange_name)
        data: TickerResponseData = {
            field: message.get(field, None) for field in ticker_format
        }
        return data

    @override
    async def _handle_message_loop(self, websocket: connect, timeout: int) -> None:
        """메시지 수신 및 처리 공통 루프

        Args:
            websocket: 웹소켓 객체
            timeout: 타임아웃 시간(초)
        """
        self.last_heartbeat_time: float = asyncio.get_event_loop().time()  # 초기화

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
                if self.request_type == "ticker":
                    cleaned_message: TickerResponseData = (
                        await self._preprocess_message(parsed_message)
                    )
                    await self._process_message(cleaned_message)
                elif self.request_type == "orderbook":
                    await self._process_message(parsed_message)

            except AsyncException:
                # 타임아웃 발생 - 하트비트 필요 확인
                current_time: float = asyncio.get_event_loop().time()
                condition: bool = (
                    current_time - self.last_heartbeat_time > self.heartbeat_interval
                )
                if condition:
                    # 설정된 시간 이상 하트비트 없으면 발송
                    await self._send_heartbeat(websocket)
                    print(f"{self.exchange_name}: 하트비트 전송")
                    self.last_heartbeat_time = current_time


class BaseKoreaWebsocketHandler(BaseWebsocketHandler, ABC):
    """한국 거래소 웹소켓 핸들러"""

    def __init__(
        self,
        event_bus: EventBus,
        exchange_name: str,
        region: str,
        request_type: str,
    ) -> None:
        super().__init__(
            event_bus=event_bus,
            exchange_name=exchange_name,
            region=region,
            request_type=request_type,
        )
        # 한국 거래소 웹소켓 핸들러의 경우 30초 간격으로 ping을 전송
        self.ping_interval = 30
        self.last_ping_time = 0

    async def process_ticker_message(self, message: Any) -> TickerResponseData:
        """
        티커 메시지 처리 함수.

        전제:
        - 일부 필드는 message 최상위에 존재하고,
        - 나머지는 message["data"] 내부에 존재합니다.

        Args:
            message: 티커 메시지 (예: {"timestamp": ..., "data": {...}})
            ticker_format: 추출할 필드 목록 (예: ["timestamp", "open", "close", "volume"])

        Returns:
            TickerResponseData: ticker_format에 해당하는 필드만 포함한 결과 dict
        """
        if isinstance(message, dict):
            coinone_type: str = message.get("response_type", "")
            if coinone_type in ["CONNECTED", "SUBSCRIBED"]:
                return None

        # data_sub에 dictionary가 있으면 update_dict를 사용하여 병합, 그렇지 않으면 원본 메시지 사용
        data_sub: dict | None = message.get("data", None)
        if data_sub and isinstance(data_sub, dict):
            message: dict = update_dict(message, "data")

        ticker_format: list[str] | None = ticker_config(self.exchange_name)
        return {field: message.get(field, None) for field in ticker_format}

    async def process_orderbook_message(self, message: Any) -> OrderbookResponseData:
        """
        오더북 메시지 처리 함수.
        각 거래소별로 구현해야 함

        Args:
            message: 오더북 메시지

        Returns:
            OrderbookResponseData: 표준화된 오더북 데이터
        """
        if not isinstance(message, dict):
            message = json.loads(message)

        return message

    @override
    async def _handle_message_loop(self, websocket: connect, timeout: int) -> None:
        """메시지 수신 및 처리 루프 (티커/오더북 모두 처리)"""
        while True:
            message = await asyncio.wait_for(websocket.recv(), timeout=timeout)
            parsed_message = json.loads(message)

            handler_map: MessageHandler = {
                "ticker": self.process_ticker_message,
                "orderbook": self.process_orderbook_message,
            }
            handler = handler_map.get(self.request_type)
            if handler:
                data: AsyncTradeType = await handler(parsed_message)
                if data:
                    await self._process_message(data)
