from adapters.base.event.event_bus import EventBus
from adapters.base.event.types import EventType, EventMetadata, TickerPayload
from common.exception.exceptions import handle_exchange_exceptions
import json
import asyncio
from typing import Any
from dataclasses import dataclass


@dataclass
class TickerHandler:
    """거래소 티커 데이터 핸들러"""

    event_bus: EventBus
    exchange_name: str

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

            # Ticker 데이터 이벤트 발행
            await self.event_bus.publish(
                EventType.MARKET_TICKER,
                TickerPayload(
                    exchange=self.exchange_name,
                    timestamp=asyncio.get_event_loop().time(),
                    data=data,
                ),
                EventMetadata(source=self.exchange_name),
            )
