from __future__ import annotations
import asyncio
from dataclasses import dataclass, field
from typing import Any, TypeVar, Generic, Optional
from datetime import datetime, timedelta

from common.logger import PipelineLogger
from adapters.base.event.types import EventPayload, EventType, EventMetadata


T = TypeVar("T")


@dataclass
class RetryConfig:
    """이벤트 재시도 설정"""

    max_retries: int = 3  # 최대 재시도 횟수
    initial_delay: float = 0.1  # 초기 지연 시간(초)
    max_delay: float = 10.0  # 최대 지연 시간(초)
    backoff_factor: float = 2.0  # 재시도 간 지연 시간 증가 계수
    jitter: float = 0.1  # 무작위 지연 범위(±)


@dataclass
class RetryEvent(Generic[T]):
    """재시도 이벤트 상태 추적"""

    event_type: EventType
    data: T
    metadata: EventMetadata
    retry_count: int = 0
    next_retry: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    error: Optional[Exception] = None

    def increment_retry(self, config: RetryConfig) -> bool:
        """재시도 횟수 증가 및 다음 재시도 시간 계산

        Args:
            config: 재시도 구성

        Returns:
            재시도 가능 여부
        """
        self.retry_count += 1
        if self.retry_count > config.max_retries:
            return False

        # 지수 백오프 계산
        delay = min(
            config.initial_delay * (config.backoff_factor ** (self.retry_count - 1)),
            config.max_delay,
        )

        # 지터 적용 (무작위성 추가)
        jitter_amount = delay * config.jitter
        delay = delay + (
            asyncio.get_event_loop().time() % (jitter_amount * 2) - jitter_amount
        )

        self.next_retry = datetime.now() + timedelta(seconds=delay)
        return True


class EventRetryManager:
    """이벤트 재시도 관리자

    이벤트 발행 시 실패한 이벤트를 추적하고 설정된 정책에 따라 재시도합니다.
    """

    def __init__(self, retry_config: RetryConfig = None) -> None:
        self.logger = PipelineLogger.get_logger("event_bus", "retry_manager")
        self.retry_config = retry_config or RetryConfig()
        self.pending_retries: list[RetryEvent] = []
        self.retry_task: Optional[asyncio.Task] = None

    async def add_retry(
        self,
        event_type: EventType,
        data: Any,
        metadata: EventMetadata,
        error: Exception,
    ) -> None:
        """재시도 대기열에 이벤트 추가

        Args:
            event_type: 이벤트 타입
            data: 이벤트 데이터
            metadata: 이벤트 메타데이터
            error: 발생한 오류
        """
        retry_event = RetryEvent(event_type, data, metadata)
        retry_event.error = error

        if retry_event.increment_retry(self.retry_config):
            self.pending_retries.append(retry_event)
            self.logger.info(
                f"이벤트 {event_type} (id: {metadata.event_id}) 재시도 예약 "
                f"(시도 {retry_event.retry_count}/{self.retry_config.max_retries})"
            )

            # 재시도 처리기 시작 (아직 실행 중이 아니라면)
            if self.retry_task is None or self.retry_task.done():
                self.retry_task = asyncio.create_task(self._retry_processor())
        else:
            self.logger.error(
                f"이벤트 {event_type} (id: {metadata.event_id}) 재시도 횟수 초과 "
                f"({self.retry_config.max_retries}회). 오류: {error}"
            )

    async def _retry_processor(self) -> None:
        """백그라운드 재시도 처리기

        이벤트 재시도 큐를 주기적으로 확인하고 재시도 시간이 된 이벤트를 처리합니다.
        """
        while self.pending_retries:
            now = datetime.now()
            ready_events = [
                e for e in self.pending_retries if e.next_retry and e.next_retry <= now
            ]

            for event in ready_events:
                self.pending_retries.remove(event)
                # 실제 재시도 로직은 EventBus에서 호출할 때 구현
                yield event

            # 남은 이벤트가 있으면 다음 재시도 대기
            if self.pending_retries:
                next_retry = min(
                    e.next_retry for e in self.pending_retries if e.next_retry
                )
                wait_time = (next_retry - now).total_seconds()
                await asyncio.sleep(max(0.1, wait_time))
            else:
                break  # 남은 재시도가 없으면 종료
