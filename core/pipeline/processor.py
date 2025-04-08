from adapters.base.event.event_bus import EventBus
from adapters.base.event.types import EventType, EventMetadata, DataPayload
from common.exceptions import handle_exchange_exceptions
import json
import asyncio
from typing import Any
from dataclasses import dataclass


@dataclass
class BaseMessageHandler:
    """거래소 데이터 핸들러 기본 클래스"""

    event_bus: EventBus
    exchange_name: str
    event_type: EventType  # 이벤트 타입을 속성으로 추가

    @handle_exchange_exceptions()  # 데코레이터 적용
    async def _process_message(self, message: Any) -> None:
        """수신된 메시지 처리 및 이벤트 발행"""
        # bytes 메시지 처리
        if isinstance(message, bytes):
            message = message.decode("utf-8")

        # JSON 문자열 처리
        if isinstance(message, str):
            # JSONDecodeError는 데코레이터에서 처리됨
            data = json.loads(message)

            # 데이터 이벤트 발행
            await self.event_bus.publish(
                self.event_type,  # 각 핸들러의 이벤트 타입 사용
                DataPayload(
                    exchange=self.exchange_name,
                    timestamp=asyncio.get_event_loop().time(),
                    data=data,
                ),
                EventMetadata(source=self.exchange_name),
            )


class TickerHandler(BaseMessageHandler):
    """거래소 티커 데이터 핸들러"""

    def __init__(self, event_bus: EventBus, exchange_name: str) -> None:
        super().__init__(
            event_bus=event_bus,
            exchange_name=exchange_name,
            event_type=EventType.MARKET_TICKER,
        )


class OrderbookHandler(BaseMessageHandler):
    """거래소 오더북 데이터 핸들러"""

    def __init__(self, event_bus: EventBus, exchange_name: str) -> None:
        super().__init__(
            event_bus=event_bus,
            exchange_name=exchange_name,
            event_type=EventType.MARKET_ORDERBOOK,
        )
