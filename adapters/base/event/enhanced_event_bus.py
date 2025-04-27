from __future__ import annotations
import asyncio
from typing import Any

from adapters.base.event.event_bus import EventBus
from adapters.base.event.types import (
    CallbackFunction,
    EventType,
    EventPayload,
    EventMetadata,
    EventBatchConfig,
)
from adapters.base.event.resilience import EventRetryManager, RetryConfig
from common.exceptions import AsyncException
from common.logger import PipelineLogger


class EnhancedEventBus(EventBus):
    """강화된 이벤트 버스 구현

    기존 EventBus의 기능을 유지하면서 다음과 같은 개선을 추가합니다:
    1. 이벤트 재시도 메커니즘
    2. 이벤트 흐름 추적 및 디버깅
    3. 에러 처리 강화
    """

    def __init__(
        self,
        batch_config: EventBatchConfig = None,
        retry_config: RetryConfig = None,
        enable_tracing: bool = False,
    ) -> None:
        """강화된 이벤트 버스 초기화"""
        super().__init__(batch_config)

        # 로깅 설정
        self.logger = PipelineLogger.get_logger("event_bus", "enhanced")

        # 재시도 관리자 초기화
        self.retry_manager = EventRetryManager(retry_config)

        # 흐름 추적 설정
        self.enable_tracing = enable_tracing
        self.event_traces: dict[str, list[dict]] = {}

        # 병렬 이벤트 처리를 위한 컨텍스트
        self.publish_semaphore = asyncio.Semaphore(10)  # 동시 처리 이벤트 제한

    async def publish(
        self,
        event_type: EventType | str,
        data: Any = None,
        metadata: EventMetadata = None,
        retry_on_failure: bool = True,
    ) -> None:
        """이벤트 발행 및 모든 구독자에게 비동기 전파

        Args:
            event_type: 발행할 이벤트 타입 (Enum 또는 문자열)
            data: 이벤트와 함께 전달할 데이터
            metadata: 이벤트 메타데이터 (우선순위, 소스 등 포함)
            retry_on_failure: 이벤트 처리 실패 시 재시도 여부
        """
        # 백프레셔 적용 - 동시 이벤트 수 제한
        async with self.publish_semaphore:
            try:
                # 이벤트 발행 로깅
                event_key = self.event_type_registry.get_event_key(event_type)

                # 기본 메타데이터 생성
                if metadata is None:
                    evt_type = self.event_type_registry.get_event_type(event_key)
                    metadata = EventMetadata(
                        source="EnhancedEventBus", extra={"event_type": evt_type}
                    )

                # 이벤트 추적 추가 (활성화된 경우)
                if self.enable_tracing:
                    self._add_trace(
                        event_key,
                        metadata.event_id,
                        "publish",
                        {
                            "data_type": type(data).__name__,
                            "metadata": metadata.__dict__,
                        },
                    )

                # 이벤트 페이로드 생성
                payload = EventPayload(data=data, metadata=metadata)

                # 구독자에게 이벤트 전파
                await self._process_event(event_key, payload)

            except AsyncException as e:
                self.logger.error(f"이벤트 {event_type} 발행 오류: {e}")

                # 재시도 설정이 활성화된 경우
                if retry_on_failure:
                    await self.retry_manager.add_retry(event_type, data, metadata, e)
                else:
                    # 재시도 없이 실패 처리
                    self.logger.warning(f"이벤트 {event_type} 재시도 없이 실패")

    async def _process_event(self, event_key: str, payload: EventPayload) -> None:
        """개별 이벤트 처리 및 구독자에게 전달

        Args:
            event_key: 이벤트 키
            payload: 이벤트 페이로드
        """
        # 이벤트 타입에 대한 구독자 목록 복사본 가져오기
        subscribers = self.subscription_manager.get_subscribers(event_key)
        if not subscribers:
            # 구독자가 없는 경우 추적만 추가하고 종료
            if self.enable_tracing:
                self._add_trace(
                    event_key, payload.metadata.event_id, "no_subscribers", {}
                )
            return

        self.logger.debug(f"발행된 이벤트 '{event_key}'의 구독자 {len(subscribers)}명")

        # 추적 추가 (활성화된 경우)
        if self.enable_tracing:
            self._add_trace(
                event_key,
                payload.metadata.event_id,
                "processing",
                {"subscriber_count": len(subscribers)},
            )

        # 모든 구독자에게 비동기적으로 이벤트 전파
        # 각 콜백은 개별 태스크로 실행되므로 한 콜백의 지연/오류가 다른 콜백에 영향 주지 않음
        await asyncio.gather(
            *[
                self._safe_callback(
                    callback, payload.data, event_key, payload.metadata.event_id
                )
                for callback in subscribers
            ]
        )

    async def _safe_callback(
        self, callback: CallbackFunction, data: Any, event_key: str, event_id: str
    ) -> None:
        """안전한 콜백 실행 (예외 처리 포함)

        Args:
            callback: 실행할 콜백 함수
            data: 콜백에 전달할 데이터
            event_key: 이벤트 키 (추적용)
            event_id: 이벤트 ID (추적용)
        """
        try:
            # 추적 추가 (활성화된 경우)
            if self.enable_tracing:
                callback_name = getattr(callback, "__name__", str(callback))
                self._add_trace(
                    event_key, event_id, "callback_start", {"callback": callback_name}
                )

            # 콜백 함수 호출 및 결과 획득
            result = callback(data)
            # 콜백이 Future를 반환하면 완료될 때까지 대기
            if asyncio.isfuture(result):
                await result
            elif asyncio.iscoroutine(result):
                await result

            # 성공 추적 추가
            if self.enable_tracing:
                callback_name = getattr(callback, "__name__", str(callback))
                self._add_trace(
                    event_key, event_id, "callback_success", {"callback": callback_name}
                )

        except AsyncException as e:
            # 오류 로깅
            callback_name = getattr(callback, "__name__", str(callback))
            error_msg = f"콜백 {callback_name} 실행 중 오류 (이벤트: {event_key}): {e}"
            self.logger.error(error_msg)

            # 오류 추적 추가
            if self.enable_tracing:
                self._add_trace(
                    event_key,
                    event_id,
                    "callback_error",
                    {"callback": callback_name, "error": str(e)},
                )

    def _add_trace(self, event_key: str, event_id: str, stage: str, data: dict) -> None:
        """이벤트 처리 추적 정보 추가

        Args:
            event_key: 이벤트 키
            event_id: 이벤트 ID
            stage: 처리 단계
            data: 추가 데이터
        """
        if event_id not in self.event_traces:
            self.event_traces[event_id] = []

        # 현재 시간과 이벤트 처리 단계 추가
        trace_entry = {
            "timestamp": asyncio.get_event_loop().time(),
            "event_key": event_key,
            "stage": stage,
            **data,
        }
        self.event_traces[event_id].append(trace_entry)

        # 추적 정보가 너무 많아지는 것 방지
        if len(self.event_traces) > 1000:
            # 가장 오래된 항목 50개 제거
            oldest_keys = sorted(
                self.event_traces.keys(),
                key=lambda k: self.event_traces[k][0]["timestamp"],
            )[:50]
            for key in oldest_keys:
                del self.event_traces[key]

    def get_event_trace(self, event_id: str) -> list[dict] | None:
        """특정 이벤트의 처리 추적 정보 가져오기

        Args:
            event_id: 이벤트 ID

        Returns:
            추적 정보 리스트 또는 None (이벤트가 없는 경우)
        """
        return self.event_traces.get(event_id)

    def clear_event_traces(self) -> None:
        """모든 이벤트 추적 정보 삭제"""
        self.event_traces.clear()

    async def process_retries(self) -> None:
        """재시도 대기열의 이벤트 처리

        현재 재시도할 시간이 된 이벤트를 발행합니다.
        """
        retry_processor = self.retry_manager._retry_processor()
        async for event in retry_processor:
            # 재시도 이벤트 발행
            self.logger.info(
                f"이벤트 {event.event_type} (id: {event.metadata.event_id}) 재시도 "
                f"(시도: {event.retry_count})"
            )
            await self.publish(
                event.event_type,
                event.data,
                event.metadata,
                # 마지막 재시도인 경우 더 이상 재시도하지 않음
                retry_on_failure=(
                    event.retry_count < self.retry_manager.retry_config.max_retries
                ),
            )

    async def start(self) -> None:
        """이벤트 버스 시작 시스템 시작 이벤트 발행"""
        self.logger.info("강화된 이벤트 버스 시작")
        # 시스템 시작 이벤트 발행
        await self.publish(EventType.SYSTEM_STARTUP, None)

        # 재시도 처리기 시작
        asyncio.create_task(self._retry_loop())

    async def _retry_loop(self) -> None:
        """백그라운드에서 지속적으로 재시도 큐 처리"""
        while True:
            try:
                await self.process_retries()
                # 재시도 큐가 비어있으면 잠시 대기
                await asyncio.sleep(1.0)
            except Exception as e:
                self.logger.error(f"재시도 루프 오류: {e}")
                await asyncio.sleep(5.0)  # 오류 발생 시 더 긴 대기

    async def stop(self) -> None:
        """이벤트 버스 정지 시스템 종료 이벤트 발행"""
        self.logger.info("강화된 이벤트 버스 정지 중")
        # 시스템 종료 이벤트 발행
        await self.publish(EventType.SYSTEM_SHUTDOWN, None, retry_on_failure=False)
        self.logger.info("강화된 이벤트 버스 정지 완료")
