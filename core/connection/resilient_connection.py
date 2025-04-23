import asyncio
import time
from typing import Any, Callable, Awaitable
import websockets
from websockets.exceptions import ConnectionClosed

from common.exceptions import AsyncException
from common.logger import PipelineLogger
from adapters.base.event.event_bus import EventBus
from adapters.base.event.types import (
    EventType,
    ConnectionRetryPayload,
    ConnectionMaxRetryPayload,
    ConnectionSuccessPayload,
    ConnectionFailurePayload,
)


class ResilientConnection:
    """견고한 네트워크 연결 관리자

    주요 기능:
    1. 자동 재연결 메커니즘
    2. 연결 상태 모니터링
    3. 재연결 상태 이벤트 발행
    """

    def __init__(
        self,
        event_bus: EventBus,
        exchange_name: str,
        request_type: str,
    ) -> None:
        self.logger = PipelineLogger.get_logger("connection", "resilient")
        self.logger.set_context(exchange=exchange_name, request_type=request_type)
        self.event_bus = event_bus
        self.exchange_name = exchange_name
        self.request_type = request_type

        # 재연결 설정
        self.max_retries = 5
        self.retry_delay = 1.0  # 초기 지연(초)
        self.max_retry_delay = 60.0  # 최대 지연(초)
        self.backoff_factor = 2.0  # 다음 재시도의 지연 증가 팩터

        # 연결 상태
        self.connection_attempts = 0
        self.last_connected_time = 0
        self.active_connection = None

    async def connect_with_retry(
        self,
        uri: str,
        on_connect: Callable[[websockets.WebSocketClientProtocol], Awaitable[None]],
        on_message: Callable[[Any], Awaitable[None]],
        connection_params: dict[str, Any] | None = None,
    ) -> None:
        """자동 재연결 로직을 포함한 웹소켓 연결 시도

        Args:
            uri: 웹소켓 연결 URI
            on_connect: 연결 성공 시 호출될 콜백 함수
            on_message: 메시지 수신 시 호출될 콜백 함수
            connection_params: 연결 매개변수 (ping_interval, ping_timeout 등)
        """
        connection_params = connection_params or {}
        default_params = {
            "ping_interval": 30,
            "ping_timeout": 60,
        }
        # 기본값과 사용자 정의 매개변수 병합
        params = {**default_params, **connection_params}

        self.connection_attempts = 0
        retry_delay = self.retry_delay

        while self.connection_attempts <= self.max_retries:
            try:
                # 연결 시도 카운터 증가
                self.connection_attempts += 1

                # 연결 시간 측정 시작
                start_time = time.time()
                self.logger.info(f"연결 시도 #{self.connection_attempts} - {uri}")

                # 웹소켓 연결
                async with websockets.connect(uri=uri, **params) as websocket:
                    # 연결 시간 측정 종료
                    elapsed = time.time() - start_time
                    self.logger.info(f"연결 성공 ({elapsed:.2f}초)")

                    # 연결 성공 이벤트 발행
                    await self.event_bus.publish(
                        EventType.CONNECTION_SUCCESS,
                        ConnectionSuccessPayload(
                            exchange_name=self.exchange_name,
                            request_type=self.request_type,
                        ),
                    )

                    # 연결 상태 갱신
                    self.active_connection = websocket
                    self.last_connected_time = time.time()
                    self.connection_attempts = 0  # 연결 성공 시 재시도 카운터 초기화

                    # 연결 후 콜백 실행
                    await on_connect(websocket)

                    # 메시지 처리 루프
                    while True:
                        try:
                            # 메시지 수신
                            message = await websocket.recv()

                            # 메시지 처리
                            await on_message(message)
                        except AsyncException as e:
                            self.logger.warning(f"연결 종료 - {e}")
                            # 연결 종료로 인한 재연결 필요
                            break

                    # 연결 종료됨 - 재연결 시도
                    self.active_connection = None

            except AsyncException as e:
                # 연결 시간 측정 종료
                elapsed = time.time() - start_time
                self.logger.error(f"연결 실패 ({elapsed:.2f}초) - {e}")

                # 연결 실패 이벤트 발행
                await self.event_bus.publish(
                    EventType.CONNECTION_FAILURE,
                    ConnectionFailurePayload(
                        exchange_name=self.exchange_name,
                        error=str(e),
                        retry_count=self.connection_attempts,
                        request_type=self.request_type,
                    ),
                )

                if self.connection_attempts < self.max_retries:
                    # 재연결 이벤트 발행
                    await self.event_bus.publish(
                        EventType.CONNECTION_RETRY,
                        ConnectionRetryPayload(
                            exchange_name=self.exchange_name,
                            attempt=self.connection_attempts,
                            error=str(e),
                            max_retries=self.max_retries,
                        ),
                    )

                    # 지수 백오프를 사용한 대기 시간 계산
                    retry_delay = min(
                        retry_delay * self.backoff_factor, self.max_retry_delay
                    )
                    self.logger.info(f"{retry_delay:.1f}초 후 재연결 시도")
                    await asyncio.sleep(retry_delay)
                else:
                    # 최대 재시도 횟수 초과 이벤트 발행
                    await self.event_bus.publish(
                        EventType.CONNECTION_MAX_RETRY,
                        ConnectionMaxRetryPayload(
                            exchange_name=self.exchange_name,
                            max_retries=self.max_retries,
                            error=str(e),
                        ),
                    )
                    self.logger.error(
                        f"최대 재연결 횟수({self.max_retries})를 초과하였습니다."
                    )
                    break

        return None  # 모든 재시도 실패

    def is_connected(self) -> bool:
        """현재 연결 상태 확인

        Returns:
            연결 상태 (연결됨: True, 연결되지 않음: False)
        """
        return self.active_connection is not None

    async def close(self) -> None:
        """현재 연결 종료"""
        if self.active_connection:
            await self.active_connection.close()
            self.active_connection = None
            self.logger.info("연결 닫기 성공")
