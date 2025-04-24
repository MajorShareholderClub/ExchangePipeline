from __future__ import annotations
import asyncio
import logging
from typing import Any

from common.exceptions import AsyncException
from adapters.base.event.types import (
    CallbackFunction,
    EventType,
    EventPayload,
    EventMetadata,
    EventBatchConfig,
)

# 컴포넌트 임포트
from adapters.base.interface.event_interfaces import IEventBus
from adapters.base.event.event_process import (
    EventTypeRegistry,
    EventSubscriptionManager,
)


class EventBus(IEventBus):
    """이벤트 기반 메시징 시스템"""

    def __init__(self, batch_config: EventBatchConfig = None) -> None:
        """EventBus 초기화"""
        # 로깅 설정
        self.logger = logging.getLogger("EventBus")

        # 컴포넌트 초기화
        self.event_type_registry = EventTypeRegistry()
        self.subscription_manager = EventSubscriptionManager(self.event_type_registry)

    async def subscribe(
        self, event_type: EventType | str, callback: CallbackFunction
    ) -> None:
        """특정 이벤트 타입에 콜백 함수 등록

        Args:
            event_type: 구독할 이벤트 타입 (Enum 또는 문자열)
            callback: 이벤트 발생 시 호출될 비동기 콜백 함수
        """
        await self.subscription_manager.subscribe(event_type, callback)

    async def unsubscribe(
        self, event_type: EventType | str, callback: CallbackFunction
    ) -> None:
        """이벤트 타입에서 콜백 함수 등록 해제

        Args:
            event_type: 구독 취소할 이벤트 타입 (Enum 또는 문자열)
            callback: 구독 취소할 콜백 함수
        """
        await self.subscription_manager.unsubscribe(event_type, callback)

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
            retry_on_failure: 이벤트 처리 실패 시 재시도 여부 (기본 구현에서는 사용하지 않음)
        """
        event_key = self.event_type_registry.get_event_key(event_type)

        # 이벤트 페이로드 생성
        if metadata is None:
            # 기본 메타데이터 생성
            evt_type = self.event_type_registry.get_event_type(event_key)
            # 시스템 이벤트는 높은 우선순위로 처리
            metadata = EventMetadata(source="EventBus", extra={"event_type": evt_type})

        payload = EventPayload(data=data, metadata=metadata)

        # 즉시 처리 (배치 처리 없이)
        await self._process_event(event_key, payload)

    async def _process_event(self, event_key: str, payload: EventPayload) -> None:
        """개별 이벤트 처리 및 구독자에게 전달

        Args:
            event_key: 이벤트 키
            payload: 이벤트 페이로드
        """
        # 이벤트 타입에 대한 구독자 목록 복사본 가져오기
        subscribers = self.subscription_manager.get_subscribers(event_key)
        if not subscribers:
            return

        self.logger.debug(
            f"Published event '{event_key}' to {len(subscribers)} subscribers"
        )

        # 모든 구독자에게 비동기적으로 이벤트 전파
        # 각 콜백은 개별 태스크로 실행되므로 한 콜백의 지연/오류가 다른 콜백에 영향 주지 않음
        await asyncio.gather(
            *[self._safe_callback(callback, payload.data) for callback in subscribers]
        )

    async def _safe_callback(self, callback: CallbackFunction, data: Any) -> None:
        """안전한 콜백 실행 (예외 처리 포함)

        Args:
            callback: 실행할 콜백 함수
            data: 콜백에 전달할 데이터
        """
        try:
            # 콜백 함수 호출 및 결과 획득
            result = callback(data)
            # 콜백이 Future를 반환하면 완료될 때까지 대기
            if asyncio.isfuture(result):
                await result
            elif asyncio.iscoroutine(result):
                await result
        except AsyncException as e:
            self.logger.error(f"Error occurred during event processing: {e}, {data}")

    async def start(self) -> None:
        """이벤트 버스 시작 시스템 시작 이벤트 발행"""
        self.logger.info("Starting EventBus")
        # 시스템 시작 이벤트 발행
        await self.publish(EventType.SYSTEM_STARTUP, None)

    async def stop(self) -> None:
        """이벤트 버스 정지 시스템 종료 이벤트 발행"""
        self.logger.info("Stopping EventBus")
        # 시스템 종료 이벤트 발행
        await self.publish(EventType.SYSTEM_SHUTDOWN, None)

        self.logger.info("EventBus stopped")
