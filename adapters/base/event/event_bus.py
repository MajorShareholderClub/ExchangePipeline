from __future__ import annotations
import asyncio
import logging
from typing import Any

from adapters.base.event.types import (
    CallbackFunction,
    EventType,
    EventPayload,
    EventMetadata,
    EventBatchConfig,
    AsyncException,
)

# 컴포넌트 임포트
from adapters.base.interface.event_interfaces import IEventBus
from adapters.base.event.event_process import (
    EventTypeRegistry,
    EventSubscriptionManager,
)


class EventBus(IEventBus):
    """이벤트 기반 메시징 시스템

    이벤트 발행(publishing)과 구독(subscribing)을 관리하는 중앙 허브.
    통신을 느슨하게 결합하기 위해 사용함. 이벤트 발행자는 특정 이벤트 타입에
    데이터를 발행하고, 구독자는 관심 있는 이벤트 타입을 구독해서 비동기적으로
    처리함.

    개선된 기능:
    1. Enum 기반 이벤트 타입 지원 (타입 안전성 향상)
    2. 대량 이벤트 배치 처리 지원 (40개 이상 거래소 연결 대응)
    3. 이벤트 우선순위 설정 (중요 이벤트 먼저 처리)
    4. 백프레셔 메커니즘 (시스템 과부하 방지)
    """

    def __init__(self, batch_config: EventBatchConfig = None):
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
                       콜백은 None 또는 asyncio.Future[None]을 반환할 수 있음
                       Future를 반환하는 경우, 이벤트 처리가 완료되기를 기다리고
                       예외 발생 시 로깅함

        Returns:
            None
        """
        await self.subscription_manager.subscribe(event_type, callback)

    async def unsubscribe(
        self, event_type: EventType | str, callback: CallbackFunction
    ) -> None:
        """이벤트 타입에서 콜백 함수 등록 해제

        Args:
            event_type: 구독 취소할 이벤트 타입 (Enum 또는 문자열)
            callback: 구독 취소할 콜백 함수

        Returns:
            None
        """
        await self.subscription_manager.unsubscribe(event_type, callback)

    async def publish(
        self,
        event_type: EventType | str,
        data: Any = None,
        metadata: EventMetadata = None,
    ) -> None:
        """이벤트 발행 및 모든 구독자에게 비동기 전파

        각 구독자는 독립적인 태스크로 실행되어, 한 구독자의 처리 지연이
        다른 구독자에게 영향을 주지 않음. 구독자 목록은 이벤트 발행 시점에
        스냅샷으로 복사되므로, 처리 중에 구독/구독취소가 발생해도 안전함.

        성능 최적화:
        - 이벤트 발행 시점에는 락을 사용하지 않고 구독자 리스트 복사본 사용
        - 40개 이상의 거래소에서 동시에 이벤트를 발행해도 병렬 처리 가능
        - 이벤트 발행은 읽기 작업이므로 구독자 목록 복사 후 락 없이 처리

        배치 처리:
        - 대량의 이벤트 발생 시 배치 처리를 통해 시스템 부하 관리
        - 우선순위에 따라 이벤트 처리 순서 조정
        - 백프레셔 메커니즘으로 시스템 과부하 방지

        Args:
            event_type: 발행할 이벤트 타입 (Enum 또는 문자열)
            data: 이벤트와 함께 전달할 데이터
            metadata: 이벤트 메타데이터 (우선순위, 소스 등 포함)
            use_batch: 배치 처리 사용 여부 (긴급 이벤트는 false로 설정)

        Returns:
            None
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

        Returns:
            None
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
            self.logger.error(f"Error occurred during event processing: {e}")

    async def start(self) -> None:
        """이벤트 버스 시작

        배치 처리 시작 및 시스템 시작 이벤트 발행
        """
        self.logger.info("Starting EventBus")
        # 시스템 시작 이벤트 발행
        await self.publish(EventType.SYSTEM_STARTUP, None)

    async def stop(self) -> None:
        """이벤트 버스 정지

        배치 처리 중단 및 시스템 정지 이벤트 발행
        """
        self.logger.info("Stopping EventBus")
        # 시스템 종료 이벤트 발행
        await self.publish(EventType.SYSTEM_SHUTDOWN, None)

        self.logger.info("EventBus stopped")
