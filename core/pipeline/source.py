# 데이터 소스(거래소 웹소켓 연결) 관련 코드
import json
import asyncio
import websockets
from dataclasses import dataclass

from typing import Any
from abc import ABC, abstractmethod
from common.exceptions import handle_exchange_exceptions
from adapters.base.event.types import (
    EventType,
    EventMetadata,
    ConnectPayload,
    DataPayload,
)
from adapters.base.event.event_bus import EventBus

import logging

logger = logging.getLogger("websocket_handler")

# 단일 출력용 로거 설정 - 중복 방지를 위한 별도 로거
single_logger = logging.getLogger("single_output")
_handler = logging.StreamHandler()
_formatter = logging.Formatter("%(asctime)s - INFO - %(message)s")
_handler.setFormatter(_formatter)
single_logger.addHandler(_handler)
single_logger.setLevel(logging.INFO)
single_logger.propagate = False  # 다른 로거로 전파 방지


@dataclass
class BaseMessageHandler:
    """거래소 데이터 핸들러 기본 클래스"""

    event_bus: EventBus
    region: str
    exchange_name: str
    request_type: str
    event_type: EventType  # 이벤트 타입을 속성으로 추가

    @handle_exchange_exceptions()
    async def _process_message(self, message: Any) -> None:
        """수신된 메시지 처리 및 이벤트 발행"""
        # 데이터 이벤트 발행
        await self.event_bus.publish(
            self.event_type,  # 각 핸들러의 이벤트 타입 사용
            DataPayload(
                region=self.region,
                exchange=self.exchange_name,
                request_type=self.request_type,
                timestamp=asyncio.get_event_loop().time(),
                data=message,
            ),
            EventMetadata(source=f"{self.exchange_name}_{self.request_type}"),
        )


class BaseWebsocketHandler(BaseMessageHandler, ABC):
    """웹소켓 핸들러 추상 기본 클래스"""

    REQUEST_EVENT_TYPE_MAP = {
        "ticker": EventType.MARKET_TICKER,
        "orderbook": EventType.MARKET_ORDERBOOK,
    }

    def __init__(
        self,
        event_bus: EventBus,
        exchange_name: str,
        region: str,
        request_type: str,
    ) -> None:
        event_type: EventType | None = self.REQUEST_EVENT_TYPE_MAP.get(request_type)
        if not event_type:
            raise ValueError(f"Invalid request type: {request_type}")

        super().__init__(
            event_bus=event_bus,
            exchange_name=exchange_name,
            region=region,
            event_type=event_type,
            request_type=request_type,
        )

    async def _event_publish(self, status: str) -> None:
        """연결 상태 이벤트를 발행합니다"""
        await self.event_bus.publish(
            EventType.EXCHANGE_CONNECT,
            ConnectPayload(
                exchange=self.exchange_name,
                status=status,
                request_type=self.request_type,
            ),
            EventMetadata(source=f"{self.exchange_name}_{self.request_type}"),
        )

    async def _sending_socket_parameter(self, params: dict[str, Any]) -> str:
        """구독 메시지 준비"""
        return json.dumps(params)

    @abstractmethod
    async def _handle_message_loop(self, websocket, timeout: int) -> None:
        """메시지 수신 및 처리 루프 - 각 거래소별로 구현 필요"""
        raise NotImplementedError()

    @handle_exchange_exceptions()
    async def connect_and_subscribe(self, config: dict[str, Any]) -> None:
        """웹소켓에 연결하고 티커 데이터를 구독합니다. 공통 연결 로직 구현"""
        url: str = config["url"]
        socket_parameters: dict | list = config["parameters"]
        timeout: int = config["timeout"]

        if not socket_parameters:
            logger.warning(f"{self.exchange_name}: 소켓 파라미터가 없습니다.")
            return

        # 연결 시작 이벤트 발행
        await self._event_publish("connecting")
        logger.info(f"{self.exchange_name}: 연결 시도 중... {url}")

        async with websockets.connect(
            uri=url,
            ping_interval=30,
            ping_timeout=60,
        ) as websocket:
            logger.info(f"{self.exchange_name}: 연결 성공")

            # 연결 성공 이벤트 발행
            await self._event_publish("connected")

            # 파라미터 전송 - 거래소별 구현으로 위임
            subscription_message = await self._sending_socket_parameter(
                socket_parameters
            )
            await websocket.send(subscription_message)
            # 별도 로거를 사용하여 로그 중복 출력을 방지합니다.
            single_logger.info(f"{self.exchange_name}: 구독 파라미터 전송 완료")

            # 메시지 수신 및 처리 루프 - 거래소별 구현으로 위임
            await self._handle_message_loop(websocket, timeout)
