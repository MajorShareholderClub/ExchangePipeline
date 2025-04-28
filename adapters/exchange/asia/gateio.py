import asyncio
import json
import time
from typing import Any, override
import logging
from adapters.exchange.base_handler import BaseAsiaEuropeHandler
from adapters.exchange.utils import update_dict
from adapters.base.event.event_bus import EventBus
from common.exceptions import AsyncException
from common.setting.config.yml_config import ticker_config

logger = logging.getLogger("websocket_handler")


class GateioWebsocketHandler(BaseAsiaEuropeHandler):
    """Gate.io 거래소 웹소켓 핸들러"""

    def __init__(
        self, event_bus: EventBus, exchange_name: str, region: str, request_type: str
    ) -> None:
        super().__init__(event_bus, exchange_name, region, request_type)
        # Gate.io 애플리케이션 레이어 ping 주기 (20초)
        self.heartbeat_interval = 20
        # 마지막 메시지 수신 시간 (프로토콜 & 애플리케이션 레이어 메시지 모두 포함)
        self.last_message_time = 0

    @override
    def _is_heartbeat(self, message: Any) -> bool:
        """Gate.io의 하트비트 메시지 확인

        Args:
            message: 검사할 메시지

        Returns:
            하트비트 메시지 여부
        """
        # 1. 프로토콜 레이어 ping/pong (웹소켓 라이브러리에서 자동 처리)
        # 2. 애플리케이션 레이어 ping (spot.ping 채널로 전송)
        try:
            json_msg = json.loads(message) if isinstance(message, str) else message
            return "channel" in json_msg and json_msg["channel"] == "spot.ping"
        except Exception:
            return False

    @override
    async def _handle_heartbeat(self, websocket, message: Any) -> None:
        """Gate.io의 하트비트 응답 처리

        Args:
            websocket: 웹소켓 객체
            message: 하트비트 메시지
        """
        # Gate.io 애플리케이션 레이어 핑 응답은 서버에서 자동으로 처리함
        # 단, 메시지를 받았으므로 타임스탬프 업데이트
        self.last_heartbeat_time = asyncio.get_event_loop().time()
        self.last_message_time = self.last_heartbeat_time
        logger.debug(f"{self.exchange_name}: 핑 응답 수신")

    @override
    async def _send_heartbeat(self, websocket) -> None:
        """Gate.io의 하트비트 전송

        Args:
            websocket: 웹소켓 객체
        """
        # Gate.io 애플리케이션 레이어 핑 메시지 전송
        current_time = int(time.time())  # 초 단위 시간
        ping_message = json.dumps(
            {"time": current_time, "channel": "spot.ping", "event": ""}
        )
        await websocket.send(ping_message)
        logger.debug(f"{self.exchange_name}: 애플리케이션 레이어 핑 전송")
        # 핑을 보냈을 때는 타임스탬프를 업데이트하지 않고 응답이 왔을 때 업데이트

    @override
    async def _parse_message(self, message: Any) -> dict:
        """Gate.io 특화 메시지 파싱"""
        if isinstance(message, bytes):
            message = message.decode("utf-8")

        # 모든 메시지 수신 시 타임스탬프 업데이트 (프로토콜 레이어 ping/pong 포함)
        self.last_message_time = asyncio.get_event_loop().time()

        # Gate.io는 필터링이 필요한 메시지 처리
        try:
            json_msg: dict = json.loads(message)

            # 에러 메시지 처리
            if "error" in json_msg and json_msg["error"] is not None:
                logger.error(f"Gate.io API 오류: {json_msg['error']}")
                return None

            # 핑 응답 메시지 필터링
            if "channel" in json_msg and json_msg["channel"] == "spot.ping":
                logger.debug(f"{self.exchange_name}: 핑 응답: {json_msg}")
                return None

            # 구독 확인 메시지 필터링
            if json_msg.get("event") == "subscribe":
                logger.debug(f"{self.exchange_name}: 구독 확인: {json_msg}")
                return None

            # 일반 메시지 처리
            ticker_format: list[str] = ticker_config(self.exchange_name)
            message: dict = update_dict(json_msg, "result")
            return {field: message.get(field, None) for field in ticker_format}
        except json.JSONDecodeError as e:
            logger.warning(
                f"{self.exchange_name}: JSON 파싱 실패: {message}, 오류: {e}"
            )
            return None

    @override
    async def _handle_message_loop(self, websocket, timeout: int) -> None:
        """Gate.io 메시지 수신 및 처리 루프"""
        # 초기화
        self.last_heartbeat_time = asyncio.get_event_loop().time()
        self.last_message_time = self.last_heartbeat_time

        # 프로토콜 레이어 ping/pong 자동 응답 활성화 (대부분의 웹소켓 라이브러리에서 기본 지원)
        # 이는 websockets 라이브러리에서 기본 활성화되어 있음

        while True:
            try:
                # 메시지 수신 (타임아웃 설정)
                message = await asyncio.wait_for(websocket.recv(), timeout=timeout)

                # 주기적 애플리케이션 레이어 핑 메시지 전송 검사
                current_time = asyncio.get_event_loop().time()
                if current_time - self.last_heartbeat_time > self.heartbeat_interval:
                    await self._send_heartbeat(websocket)
                    self.last_heartbeat_time = current_time

                # 메시지 처리
                if self.request_type == "ticker":
                    parsed_message = await self._parse_message(message)
                    if parsed_message:  # None이면 처리 무시
                        await self._process_message(parsed_message)
                elif self.request_type == "orderbook":
                    parsed_message = await self._parse_message(message)
                    if parsed_message:
                        await self._process_message(parsed_message)

            except AsyncException:
                # 마지막 메시지 수신 후 일정 시간이 지나면 애플리케이션 레이어 핑 전송
                current_time = asyncio.get_event_loop().time()
                if (
                    current_time - self.last_message_time > timeout * 0.8
                ):  # 타임아웃의 80%에 해당하는 시간이 지나면
                    await self._send_heartbeat(websocket)
                    logger.info(
                        f"{self.exchange_name}: 타임아웃 발생, 애플리케이션 레이어 핑 전송"
                    )
                    self.last_heartbeat_time = current_time
            except Exception as e:
                logger.error(f"{self.exchange_name}: 메시지 처리 중 예외 발생: {e}")
                # 연결 문제 가능성이 있으므로 상위 핸들러에게 예외 전파
                raise
