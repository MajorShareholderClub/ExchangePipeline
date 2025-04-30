import asyncio
import json
from typing import Any, override
import logging
from adapters.exchange.base_handler import BaseAsiaEuropeHandler
from adapters.base.event.event_bus import EventBus
from adapters.exchange.utils import update_dict


logger = logging.getLogger("websocket_handler")


class OkxWebsocketHandler(BaseAsiaEuropeHandler):
    """OKX 거래소 웹소켓 핸들러"""

    def __init__(
        self, event_bus: EventBus, exchange_name: str, region: str, request_type: str
    ) -> None:
        super().__init__(event_bus, exchange_name, region, request_type)
        # OKX 문서에 따르면 30초 이내에 메시지가 없으면 연결이 끊어짐
        # 안전하게 25초로 설정
        self.heartbeat_interval = 25

    @override
    def _is_heartbeat(self, message: str) -> bool:
        """OKX 핑 메시지 확인

        Args:
            message: 검사할 메시지

        Returns:
            핑 메시지 여부
        """
        return "ping" in message or "pong" in message

    @override
    async def _handle_heartbeat(self, websocket, message: str) -> None:
        """OKX 핑 응답 처리

        Args:
            websocket: 웹소켓 객체
            message: 핑 메시지
        """
        # 서버가 ping을 보내면 pong으로 응답
        if "ping" in message:
            pong_message = message.replace("ping", "pong")
            await websocket.send(pong_message)
            logger.debug(f"{self.exchange_name}: 핑 수신 및 퐁 응답 전송")

        # 모든 하트비트(ping/pong) 메시지 수신 시 타임스탬프 업데이트
        self.last_heartbeat_time = asyncio.get_event_loop().time()

    @override
    async def _send_heartbeat(self, websocket) -> None:
        """OKX 하트비트 전송

        Args:
            websocket: 웹소켓 객체
        """
        # OKX 문서에 따라 ping 문자열을 전송
        await websocket.send("ping")
        logger.debug(f"{self.exchange_name}: 클라이언트 핑 전송")
        # 핑을 보냈지만 아직 응답을 받지 않은 상태이므로 타임스탬프는 업데이트하지 않음
        # 응답이 오면 _handle_heartbeat에서 업데이트됨

    @override
    async def _parse_message(self, message: str) -> Any:
        """OKX 특화 메시지 파싱

        Args:
            message: 파싱할 메시지

        Returns:
            파싱된 메시지 또는 None
        """
        # 하트비트 메시지 필터링
        if "pong" in message or "ping" in message:
            return None

        # 일반 JSON 메시지 처리
        try:
            json_msg: dict = json.loads(message)

            # 구독 확인 메시지 필터링
            if json_msg.get("event") == "subscribe":
                return None

            # 채널 연결 수 관련 메시지 필터링
            if json_msg.get("event") in [
                "channel-conn-count",
                "channel-conn-count-error",
            ]:
                logger.info(f"{self.exchange_name}: {json_msg}")
                return None

            # 데이터 메시지 처리
            message: dict = update_dict(json_msg, "data")
            return message
        except json.JSONDecodeError:
            logger.warning(f"{self.exchange_name}: JSON 파싱 실패: {message}")
            return None
