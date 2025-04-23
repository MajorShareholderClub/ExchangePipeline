import asyncio
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

from adapters.base.event.event_bus import EventBus
from adapters.base.event.types.event_types import (
    EventType,
    ConnectionRequestPayload,
    ConnectionRetryPayload,
    ConnectionFailurePayload,
    ConnectionMaxRetryPayload,
    EventMetadata,
)
from common.registry import get_exchange


@dataclass
class RetryContext:
    """재시도 관련 데이터를 담는 컨텍스트 클래스"""

    exchange_name: str
    error: str
    retry_count: int
    request_type: str
    params: Optional[Dict[str, Any]] = None
    max_retries: int = 3


@dataclass
class ConnectionRetryService:
    """연결 재시도 기능을 제공하는 서비스 클래스

    이벤트 기반 아키텍처(EDA)에 맞게 구현되어 있어,
    개별 함수 호출이 아닌 이벤트 발행/구독을 통해 동작합니다.

    단일 책임 원칙(SRP)에 따라 재시도 관리 기능만 수행합니다.
    """

    event_bus: EventBus
    max_retries: int = 3
    _initialized: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        """
        동기적 초기화 작업 수행
        비동기 초기화 작업은 initialize() 메서드에서 수행
        """
        pass

    async def initialize(self) -> None:
        """
        비동기 초기화 작업 수행
        객체 생성 후 별도로 호출해야 함
        """
        if self._initialized:
            return

        # 이벤트 핸들러 등록
        await self.event_bus.subscribe(
            EventType.CONNECTION_FAILURE,
            self.handle_connection_failure,
        )

        await self.event_bus.subscribe(
            EventType.CONNECTION_RETRY, self.handle_retry_event
        )

        self._initialized = True

    async def handle_connection_failure(self, data: ConnectionFailurePayload) -> None:
        """
        연결 실패 이벤트 핸들러

        실패한 연결 요청에 대한 재시도 결정 및 처리
        """
        # 초기화 확인
        if not self._initialized:
            await self.initialize()

        # 재시도 컨텍스트 생성
        context = RetryContext(
            exchange_name=data.get("exchange_name"),
            error=data.get("error"),
            retry_count=data.get("retry_count", 0),
            request_type=data.get("request_type"),
            params=data.get("params"),
            max_retries=self.max_retries,
        )

        # 최대 재시도 횟수 확인
        if context.retry_count >= context.max_retries:
            await self._publish_max_retry_reached(context)
            return

        # 재시도 이벤트 발행
        await self.event_bus.publish(
            EventType.CONNECTION_RETRY,
            ConnectionRetryPayload(
                exchange_name=context.exchange_name,
                attempt=context.retry_count + 1,
                error=context.error,
                max_retries=context.max_retries,
                request_type=context.request_type,
                params=context.params,
            ),
            EventMetadata(source="retry_service"),
        )

    async def handle_retry_event(self, data: ConnectionRetryPayload) -> None:
        """
        재시도 이벤트 핸들러

        지수 백오프를 적용한 재시도 수행
        """
        # 초기화 확인
        if not self._initialized:
            await self.initialize()

        exchange_name = data.get("exchange_name")
        attempt = data.get("attempt", 1)
        params = data.get("params")
        request_type = data.get("request_type")

        # 지수 백오프 적용 (2^attempt 초, 최대 30초)
        delay = min(2**attempt, 30)
        await asyncio.sleep(delay)

        # 연결 요청 재발행
        await self.event_bus.publish(
            EventType.CONNECTION_REQUEST,
            ConnectionRequestPayload(
                exchange_name=exchange_name,
                request_type=request_type,
                params=params,
                retry_count=attempt,
            ),
            EventMetadata(source="retry_service"),
        )

    async def _publish_max_retry_reached(self, context: RetryContext) -> None:
        """최대 재시도 횟수 도달 시 이벤트 발행"""
        await self.event_bus.publish(
            EventType.CONNECTION_MAX_RETRY,
            ConnectionMaxRetryPayload(
                exchange_name=context.exchange_name,
                max_retries=context.max_retries,
                error=context.error,
                request_type=context.request_type,
            ),
            EventMetadata(source="retry_service"),
        )

    async def cleanup(self) -> None:
        """서비스 종료 시 이벤트 핸들러 등록 해제"""
        if not self._initialized:
            return

        # 이벤트 구독 해제
        await self.event_bus.unsubscribe(
            EventType.CONNECTION_FAILURE,
            self.handle_connection_failure,
        )

        await self.event_bus.unsubscribe(
            EventType.CONNECTION_RETRY, self.handle_retry_event
        )

        self._initialized = False
