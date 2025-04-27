from __future__ import annotations

"""core.connection.retry
--------------------------------------------------
거래소 WebSocket 재연결 로직을 담당한다.

이 모듈은 Event-Driven Architecture 를 따르며, 다음 이벤트를 구독/발행한다.

1. EventType.CONNECTION_REQUEST  – 최초 및 재시도 연결 요청 정보를 캐시
2. EventType.CONNECTION_FAILURE  – 연결 실패 시 재시도 스케줄링
3. EventType.CONNECTION_RETRY    – 재시도 시도 이벤트 (모니터링 목적)
4. EventType.CONNECTION_MAX_RETRY – 최대 재시도 초과 이벤트

Retry 정책
==========
• 기본 최대 재시도 횟수 : 3 (configurable)
• 지수 백오프(  base_delay * 2 ** (attempt-1) )
• 재시도는 개별 (exchange, request_type) 단위로 관리

설계
====
ConnectionRetryService(EventBus)
    ├─ request_cache : 최초 CONNECTION_REQUEST 페이로드 보관
    ├─ retry_tracker : 재시도 횟수 기록

구독 핸들러
    • _on_request          – CONNECTION_REQUEST 시 request_cache에 저장
    • _on_failure          – CONNECTION_FAILURE 시 재시도 스케줄링

내부 Task
    • _retry_after_delay   – delay 후 CONNECTION_RETRY & CONNECTION_REQUEST 다시 발행
"""

import asyncio
from collections import defaultdict
from dataclasses import dataclass

from adapters.base.event.types import (
    EventType,
    ConnectionRequestPayload,
    ConnectionFailurePayload,
    ConnectionRetryPayload,
    ConnectionMaxRetryPayload,
    EventMetadata,
)
from adapters.base.event.enhanced_event_bus import EnhancedEventBus
from common.logger import PipelineLogger


@dataclass(slots=True)
class RetryConfig:
    """Retry configuration parameters."""

    max_retries: int = 3
    base_delay: float = 1.0  # seconds


class ConnectionRetryService:
    """Service managing reconnection attempts for websocket handlers."""

    def __init__(
        self, event_bus: EnhancedEventBus, config: RetryConfig | None = None
    ) -> None:
        self.event_bus: EnhancedEventBus = event_bus
        self.config: RetryConfig = config or RetryConfig()

        # (exchange, request_type)  → latest ConnectionRequestPayload
        self._request_cache: dict[tuple[str, str], ConnectionRequestPayload] = {}
        # (exchange, request_type)  → current retry count
        self._retry_tracker: defaultdict[tuple[str, str], int] = defaultdict(int)

        self.logger = PipelineLogger.get_logger("connection", "retry_service")

    # ---------------------------------------------------------------------
    # 이벤트 등록 핸들러
    # ---------------------------------------------------------------------
    async def register_handlers(self) -> None:
        """Subscribe to relevant events on the bus."""
        await self.event_bus.subscribe(EventType.CONNECTION_REQUEST, self._on_request)
        await self.event_bus.subscribe(EventType.CONNECTION_FAILURE, self._on_failure)
        self.logger.info("ConnectionRetryService 핸들러 등록 완료")

    # ------------------------------------------------------------------
    # 이벤트 핸들러
    # ------------------------------------------------------------------
    async def _on_request(self, payload: ConnectionRequestPayload) -> None:
        """Cache the latest request payload for potential future retries."""
        try:
            meta = payload["metadata"]
            key = (meta["exchange_name"], meta["request_type"])
            self._request_cache[key] = payload  # 최신 정보를 유지
            # 새 요청이면 retry count 초기화 (최초 연결 또는 외부에서 새 trigger)
            self._retry_tracker.pop(key, None)
        except Exception as exc:  # pragma: no cover – defensive
            self.logger.error(f"_on_request 처리 오류: {exc}")

    async def _on_failure(self, payload: ConnectionFailurePayload) -> None:
        """Handle connection failure and schedule retries if allowed."""
        # 일부 구현체에서 'exchange' 키를 사용하므로 호환 처리
        exchange = payload.get("exchange_name") or payload.get("exchange")
        request_type = payload.get("request_type", "unknown")
        error_msg = payload.get("error", "unknown_error")
        key = (exchange, request_type)

        current_retry = self._retry_tracker[key] + 1

        if current_retry > self.config.max_retries:
            # 최대 재시도 초과 – 알림 이벤트 발행 후 종료
            await self.event_bus.publish(
                EventType.CONNECTION_MAX_RETRY,
                ConnectionMaxRetryPayload(
                    exchange_name=exchange,
                    max_retries=self.config.max_retries,
                    error=error_msg,
                    request_type=request_type,
                ),
                EventMetadata(source="ConnectionRetryService"),
                retry_on_failure=False,
            )
            self.logger.warning(
                f"[{exchange}:{request_type}] 최대 재시도({self.config.max_retries}) 초과 – 더 이상 시도하지 않음"
            )
            # cleanup cache to avoid memory leak
            self._request_cache.pop(key, None)
            self._retry_tracker.pop(key, None)
            return

        # 기록 업데이트
        self._retry_tracker[key] = current_retry

        # 지수 백오프 계산
        delay = self.config.base_delay * (2 ** (current_retry - 1))
        self.logger.warning(
            f"[{exchange}:{request_type}] 연결 실패 – {current_retry}차 재시도 예정 (지연 {delay:.1f}s): {error_msg}"
        )

        # 재시도 예정 이벤트 발행 (모니터링 목적)
        await self.event_bus.publish(
            EventType.CONNECTION_RETRY,
            ConnectionRetryPayload(
                exchange_name=exchange,
                attempt=current_retry,
                error=error_msg,
                max_retries=self.config.max_retries,
                request_type=request_type,
                parameter_info=payload.get("parameter_info"),
                socket_instance=payload.get("socket_instance"),
            ),
            EventMetadata(source="ConnectionRetryService"),
            retry_on_failure=False,
        )

        # 재시도 Task 스케줄
        asyncio.create_task(self._retry_after_delay(key, delay))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    async def _retry_after_delay(self, key: tuple[str, str], delay: float) -> None:
        """Sleep for `delay` seconds then republish cached CONNECTION_REQUEST."""
        await asyncio.sleep(delay)
        payload = self._request_cache.get(key)
        if payload is None:
            # 해당 요청 캐시가 없으면 중단 (예: 최대 재시도 초과 후 정리됨)
            self.logger.debug(f"{key} 에 대한 재시도 payload 없음 – 중단")
            return

        # retry_count 증가 반영
        payload["retry_count"] = self._retry_tracker[key]

        await self.event_bus.publish(
            EventType.CONNECTION_REQUEST,
            payload,
            EventMetadata(source="ConnectionRetryService"),
            retry_on_failure=True,
        )
        self.logger.info(
            f"[{key[0]}:{key[1]}] {self._retry_tracker[key]}차 CONNECTION_REQUEST 재발행 완료"
        )
