from __future__ import annotations
import logging
from functools import lru_cache

from adapters.base.event.types import EventType


class EventTypeRegistry:
    """이벤트 타입 변환 및 캐싱을 담당하는 클래스

    문자열과 Enum 이벤트 타입 간의 변환을 관리하고 캐싱을 통해 성능을 최적화함
    """

    def __init__(self):
        """EventTypeRegistry 초기화"""
        self.logger = logging.getLogger("EventTypeRegistry")

    def get_event_key(self, event_type: EventType | str) -> str:
        """이벤트 타입을 문자열 키로 변환

        Enum 타입과 문자열 타입을 모두 지원하기 위한 헬퍼 함수

        Args:
            event_type: 이벤트 타입 (Enum 또는 문자열)

        Returns:
            문자열 형태의 이벤트 키
        """
        if isinstance(event_type, EventType):
            return event_type.value
        return event_type

    @lru_cache(maxsize=1024)
    def get_event_type(self, event_key: str) -> EventType | None:
        """문자열 키에서 EventType Enum으로 변환 (LRU 캐싱 적용)

        Args:
            event_key: 이벤트 키 문자열

        Returns:
            EventType 또는 None (매칭되는 이벤트가 없는 경우)
        """
        return EventType.from_string(event_key)

    def clear_cache(self) -> None:
        """이벤트 타입 캐시 초기화"""
        self.get_event_type.cache_clear()
        self.logger.debug("Event type cache cleared")
