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
from common.setting.types import ExchangeMetadata
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
    async def connect_and_subscribe(
        self, metadata: ExchangeMetadata, parameter_info: dict[str, Any]
    ) -> None:
        """웹소켓에 연결하고 티커 데이터를 구독합니다. 공통 연결 로직 구현"""
        url: str = metadata["url"]
        socket_parameters: dict | list = parameter_info
        timeout: int = 60  # 기본값 설정. parameter_info에 없을 수 있음

        if not socket_parameters:
            logger.warning(f"{self.exchange_name}: 소켓 파라미터가 없습니다.")
            return

        # 연결 시작 이벤트 발행
        await self._event_publish("connecting")
        logger.info(f"{self.exchange_name}: 연결 시도 중... {url}")

        # 핑 태스크 및 애플리케이션 핑 관련 변수
        self._ping_task = None
        self._ping_stop_event = asyncio.Event()

        try:
            async with websockets.connect(uri=url) as websocket:
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

                # 한국 거래소인 경우 애플리케이션 레벨 핑 태스크 시작
                if self.exchange_name.lower() in [
                    "upbit",
                    "bithumb",
                    "coinone",
                    "korbit",
                ]:
                    self._ping_task = asyncio.create_task(
                        self._korea_exchange_ping_loop(websocket)
                    )

                # 메시지 수신 및 처리 루프 - 거래소별 구현으로 위임
                await self._handle_message_loop(websocket, timeout)
        except Exception as e:
            logger.error(f"{self.exchange_name}: 연결 중 오류 발생: {e}")
            raise

    async def _korea_exchange_ping_loop(self, websocket) -> None:
        """한국 거래소용 프로토콜 레벨 핑 전송 루프

        Args:
            websocket: 웹소켓 연결 객체
        """
        # 거래소별 핑 메시지 포맷 및 간격 정의
        ping_interval = 20  # 20초 간격 (기본값)

        # 거래소별 특수 설정
        if self.exchange_name.lower() in ["upbit", "bithumb", "coinone", "korbit"]:
            ping_interval = 60  # 업비트/빗썸 보안적 타임아웃(120초)의 절반

        logger.info(
            f"{self.exchange_name}: 프로토콜 레벨 핑 루프 시작 (간격: {ping_interval}초)"
        )

        # 첫 핑은 연결 후 ping_interval 초 후에 발송 (서버 응답에 충분한 시간 제공)
        last_ping_time = asyncio.get_event_loop().time()

        while not self._ping_stop_event.is_set():
            current_time = asyncio.get_event_loop().time()

            # 마지막 핑 이후 ping_interval 초가 지났으면 핑 전송
            if current_time - last_ping_time >= ping_interval:
                try:
                    # 애플리케이션 레벨 핑 대신 프로토콜 레벨 핑 사용
                    pong_waiter = await websocket.ping()
                    last_ping_time = current_time
                    logger.debug(f"{self.exchange_name}: 프로토콜 레벨 핑 전송 (PING)")

                    # PONG 응답 수신 대기 및 로깅 추가
                    try:
                        await asyncio.wait_for(pong_waiter, timeout=1)
                        logger.debug(f"{self.exchange_name}: PONG 응답 수신")
                    except asyncio.TimeoutError:
                        logger.warning(
                            f"{self.exchange_name}: PONG 응답 수신 실패 (타임아웃)"
                        )

                except Exception as e:
                    logger.error(f"{self.exchange_name}: 핑 전송 실패: {e}")
                    # 연결이 끊어진 경우 루프 종료
                    break

            # 짧은 간격으로 체크 (1초마다)
            try:
                await asyncio.wait_for(self._ping_stop_event.wait(), timeout=1)
            except asyncio.TimeoutError:
                pass  # 타임아웃은 정상 흐름의 일부
