import asyncio
import json
from typing import Any, override
import logging
from common.setting.config.yml_config import get_ticker_format
from adapters.exchange.base_handler import BaseAsiaEuropeHandler
from adapters.base.event.event_bus import EventBus
from adapters.exchange.utils import update_dict

logger = logging.getLogger("websocket_handler")


class OkxWebsocketHandler(BaseAsiaEuropeHandler):
    """OKX 거래소 웹소켓 핸들러"""

    def __init__(self, event_bus: EventBus, exchange_name: str) -> None:
        super().__init__(event_bus, exchange_name)
        self.heartbeat_interval = 25  # 25초마다 핑 체크

    @override
    def _is_heartbeat(self, message: Any) -> bool:
        """OKX 핑 메시지 확인

        Args:
            message: 검사할 메시지

        Returns:
            핑 메시지 여부
        """
        return "ping" in message

    @override
    async def _handle_heartbeat(self, websocket, message: Any) -> None:
        """OKX 핑 응답 처리

        Args:
            websocket: 웹소켓 객체
            message: 핑 메시지
        """
        pong_message = message.replace("ping", "pong")
        await websocket.send(pong_message)
        logger.debug(f"{self.exchange_name}: 핑-퐁 메시지 교환")
        self.last_heartbeat_time = asyncio.get_event_loop().time()

    @override
    async def _send_heartbeat(self, websocket) -> None:
        """OKX 하트비트 전송

        Args:
            websocket: 웹소켓 객체
        """
        # OKX는 일반적으로 핑 메시지를 보내지 않음
        # 하지만 필요시 여기서 구현 가능
        pass

    @override
    async def _parse_message(self, message: Any) -> Any:
        """OKX 특화 메시지 파싱

        Args:
            message: 파싱할 메시지

        Returns:
            파싱된 메시지 또는 None
        """
        # OKX는 하트비트 메시지를 보내는 경우가 있음
        if "pong" in message or "ping" in message:
            return None  # 핑/퐁 메시지는 티커 처리하지 않음

        json_msg: dict = json.loads(message)
        if json_msg.get("event") == "subscribe":
            return None  # 구독 메시지는 티커 처리하지 않음

        ticker_format: list[str] = get_ticker_format(self.exchange_name)

        message: dict = update_dict(json_msg, "data")
        return {field: message.get(field, None) for field in ticker_format}
