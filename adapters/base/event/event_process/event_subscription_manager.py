from __future__ import annotations
import asyncio
import logging
from collections import defaultdict
from contextlib import asynccontextmanager

from adapters.base.event.types import CallbackFunction, SubscribersMap, EventType
from adapters.base.event.event_process.event_type_registry import EventTypeRegistry
from adapters.base.interface.event_interfaces import ISubscriptionManager


class EventSubscriptionManager(ISubscriptionManager):
    """이벤트 구독/구독취소 관리를 담당하는 클래스

    특정 이벤트 타입에 해당하는 콜백 함수를 등록하고 관리하는 기능 제공
    """

    def __init__(self, event_type_registry: EventTypeRegistry = None) -> None:
        """이벤트 구독 관리자 초기화"""
        # 구독자 리스트 초기화 (키: 이벤트 타입, 값: 콜백 함수 리스트)
        # defaultdict를 사용해 없는 이벤트 타입에 대한 확인이 필요 없음
        self._subscribers: SubscribersMap = defaultdict(list)

        # 구독자 목록 수정 시 동시성 보호를 위한 락
        self._lock = asyncio.Lock()

        # 이벤트 타입 레지스트리
        self.event_type_registry = event_type_registry or EventTypeRegistry()

        # 로깅 설정
        self.logger = logging.getLogger("EventSubscriptionManager")

    @asynccontextmanager
    async def subscribers_lock(self):
        """구독자 락 접근 파이썬 컨텍스트 매니저

        Returns:
            락취득 후에 자동으로 해제하는 컨텍스트 매니저
        """
        await self._lock.acquire()
        try:
            yield
        finally:
            self._lock.release()

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
        """
        event_key = self.event_type_registry.get_event_key(event_type)

        # subscribers_lock 컨텍스트 매니저 활용
        async with self.subscribers_lock():
            self._subscribers[event_key].append(callback)
            self.logger.debug(f"New subscriber registered for event '{event_key}'")

    async def unsubscribe(
        self, event_type: EventType | str, callback: CallbackFunction
    ) -> None:
        """이벤트 타입에서 콜백 함수 등록 해제

        Args:
            event_type: 구독 취소할 이벤트 타입 (Enum 또는 문자열)
            callback: 구독 취소할 콜백 함수
        """
        event_key = self.event_type_registry.get_event_key(event_type)

        # 이벤트 타입이 존재하는 경우에만 락 획득 및 처리
        if event_key in self._subscribers:
            # _subscribers_lock 컨텍스트 매니저 활용
            async with self.subscribers_lock():
                if callback in self._subscribers[event_key]:
                    self._subscribers[event_key].remove(callback)
                    self.logger.debug(f"Subscriber removed from event '{event_key}'")

    def get_subscribers(self, event_key: str) -> list[CallbackFunction]:
        """특정 이벤트 타입에 대한 구독자 리스트 반환 (복사본)

        Args:
            event_key: 이벤트 타입 키

        Returns:
            구독자 콜백 함수 리스트 (복사본)
        """
        # 이벤트 타입에 대한 구독자 목록 복사본 반환
        # (처리 중 구독/구독취소가 발생해도 영향 없도록)
        subscribers = self._subscribers[event_key].copy()
        return subscribers

    def clear_subscribers(self) -> None:
        """모든 구독자 정보 제거"""
        self._subscribers.clear()
        self.logger.debug("All subscribers have been cleared")
