from __future__ import annotations
import asyncio
import logging
import time
from collections import deque, Counter
from typing import Any, Callable

from adapters.base.event.types import (
    EventPriority,
    EventPayload,
    EventBatchConfig,
    AsyncException,
)


class EventBatchProcessor:
    """이벤트 배치 프로세서

    이벤트 배치 프로세서는 이벤트를 수집하고 배치로 처리하는 역할을 합니다.
    이벤트 배치 프로세서를 사용하면 이벤트를 효율적으로 처리할 수 있습니다.
    """

    def __init__(self, batch_config: EventBatchConfig = None):
        """이벤트 배치 프로세서 초기화

        Args:
            batch_config: 이벤트 배치 프로세서 설정
        """
        # 로거 초기화
        self.logger = logging.getLogger("EventBatchProcessor")

        # 이벤트 배치 프로세서 설정 초기화
        self._batch_config = batch_config or EventBatchConfig()

        # 이벤트 큐 초기화
        self._event_queues: dict[EventPriority, deque] = {
            EventPriority.HIGH: deque(maxlen=self._batch_config.max_queue_size),
            EventPriority.MEDIUM: deque(maxlen=self._batch_config.max_queue_size),
            EventPriority.LOW: deque(maxlen=self._batch_config.max_queue_size),
        }

        # 이벤트 배치 프로세서 상태 초기화
        self._batch_processing = False
        self._batch_task = None

        # 이벤트 처리 콜백 함수 초기화
        self._process_event_callback = None

        # 메트릭 카운터 초기화
        self._metrics = {
            "dropped_events": Counter(),
            "downgraded_events": 0,
            "processed_events": 0,
        }

        # 로깅 샘플링 비율 (1/N)
        self._log_sample_rate = 100  # 100개 중 1개만 로깅
        self._event_counter = 0

    def set_process_event_callback(
        self, callback: Callable[[str, EventPayload], Any]
    ) -> None:
        """이벤트 처리 콜백 함수 설정

        Args:
            callback: 이벤트 처리 콜백 함수
        """
        self._process_event_callback = callback

    def add_to_batch_queue(self, event_key: str, payload: EventPayload) -> None:
        """이벤트를 배치 큐에 추가

        Args:
            event_key: 이벤트 키
            payload: 이벤트 페이로드
        """
        priority = payload.metadata.priority
        self._event_counter += 1
        should_log = self._event_counter % self._log_sample_rate == 0

        # 이벤트 큐가 가득 찼을 때
        if len(self._event_queues[priority]) >= self._batch_config.max_queue_size:
            if should_log:
                self.logger.debug(f"Queue full for {priority}, applying backpressure")

            # 이벤트를 버림
            if priority == EventPriority.LOW:
                self._metrics["dropped_events"]["LOW"] += 1
                return

            # 이벤트를 낮은 우선순위로 다운그레이드
            elif priority == EventPriority.MEDIUM:
                # 낮은 우선순위 이벤트 큐가 가득 찼을 때
                priority_len = len(self._event_queues[EventPriority.LOW])
                if priority_len >= self._batch_config.max_queue_size:
                    self._metrics["dropped_events"]["MEDIUM"] += 1
                    return

                # 이벤트를 낮은 우선순위로 다운그레이드
                priority = EventPriority.LOW
                payload.metadata.priority = priority
                self._metrics["downgraded_events"] += 1

        # 이벤트를 큐에 추가
        self._event_queues[priority].append((event_key, payload))

        # 이벤트 배치 프로세서를 시작
        if not self._batch_processing:
            self._start_batch_processing()

        # 주기적으로 메트릭 로깅
        if should_log and any(self._metrics["dropped_events"].values()):
            self.logger.warning(
                f"Backpressure metrics: dropped={dict(self._metrics['dropped_events'])}, "
                f"downgraded={self._metrics['downgraded_events']}"
            )

    def _start_batch_processing(self) -> None:
        """이벤트 배치 프로세서를 시작"""
        if self._batch_processing:
            return

        self._batch_processing = True
        self._batch_task = asyncio.create_task(self._batch_process_events())
        self._batch_task.add_done_callback(self._on_batch_task_done)

    def _on_batch_task_done(self, task: asyncio.Task) -> None:
        """이벤트 배치 프로세서가 완료되었을 때"""
        self._batch_processing = False
        # 이벤트 배치 프로세서가 실패했을 때
        if task.exception() is not None:
            self.logger.error(f"Batch processing task failed: {task.exception()}")

        # 이벤트 큐가 비어있지 않을 때
        if any(len(q) > 0 for q in self._event_queues.values()):
            self._start_batch_processing()

    async def _batch_process_events(self) -> None:
        """이벤트 배치 프로세서"""
        while any(len(q) > 0 for q in self._event_queues.values()):
            start_time = time.time()
            batch_count = 0

            # 이벤트를 우선순위별로 처리
            for priority in sorted(self._event_queues.keys(), key=lambda p: p.value):
                queue: deque = self._event_queues[priority]

                # 이벤트를 배치로 처리
                remaining: int = self._batch_config.batch_size - batch_count
                process_count: int = min(remaining, len(queue))

                if process_count <= 0:
                    break

                # 이벤트를 배치로 처리
                batch_events = []
                for _ in range(process_count):
                    if queue:
                        batch_events.append(queue.popleft())
                    else:
                        break

                # 이벤트를 처리
                tasks = [
                    asyncio.create_task(
                        self._safe_callback(
                            self._process_event_callback, event_key, payload
                        )
                    )
                    for event_key, payload in batch_events
                    if self._process_event_callback
                ]

                # 이벤트를 처리
                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)

                batch_count += len(tasks)
                self._metrics["processed_events"] += len(tasks)

                # 이벤트 배치 프로세서를 완료
                if batch_count >= self._batch_config.batch_size:
                    break

            # 이벤트 배치 프로세서를 완료
            elapsed = time.time() - start_time
            if elapsed < self._batch_config.flush_interval and batch_count > 0:
                await asyncio.sleep(self._batch_config.flush_interval - elapsed)

    async def _safe_callback(self, callback: Callable, *args, **kwargs) -> None:
        """이벤트 처리 콜백 함수를 안전하게 호출

        Args:
            callback: 이벤트 처리 콜백 함수
            *args: 이벤트 처리 콜백 함수의 인자
            **kwargs: 이벤트 처리 콜백 함수의 키워드 인자
        """
        try:
            # 이벤트 처리 콜백 함수를 호출
            result = callback(*args, **kwargs)
            # 이벤트 처리 콜백 함수가 코루틴일 때
            if asyncio.iscoroutine(result) or asyncio.isfuture(result):
                await result
        except AsyncException as e:
            # 필요한 경우에만 오류 로깅
            if hasattr(e, "should_log") and e.should_log:
                self.logger.error(f"Error during event processing: {e}")
            else:
                self.logger.debug(f"Event processing error: {type(e).__name__}")

    async def stop(self) -> None:
        """이벤트 배치 프로세서를 중지"""
        # 이벤트 배치 프로세서를 중지
        if self._batch_task and not self._batch_task.done():
            self._batch_task.cancel()
            try:
                await self._batch_task
            except asyncio.CancelledError:
                pass

        self._batch_processing = False

        # 이벤트 큐를 초기화
        for priority in self._event_queues:
            self._event_queues[priority].clear()

        if self._metrics["processed_events"] > 0:
            self.logger.info(
                f"Batch processor stopped, processed {self._metrics['processed_events']} events"
            )

    def is_processing(self) -> bool:
        """이벤트 배치 프로세서가 처리 중인지 확인"""
        return self._batch_processing
