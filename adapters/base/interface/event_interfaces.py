from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any

from adapters.base.event.types import (
    EventType,
    EventMetadata,
    EventPayload,
    CallbackFunction,
)


class IEventTypeRegistry(ABC):
    """이벤트 타입 변환 및 관리를 위한 인터페이스

    이벤트 타입과 문자열 간의 변환을 관리하는 인터페이스 정의
    """

    @abstractmethod
    def get_event_key(self, event_type: EventType | str) -> str:
        """이벤트 타입을 문자열 키로 변환

        Args:
            event_type: 이벤트 타입 (Enum 또는 문자열)

        Returns:
            문자열 형태의 이벤트 키
        """
        raise NotImplementedError()

    @abstractmethod
    def get_event_type(self, event_key: str) -> EventType | None:
        """문자열 키에서 EventType Enum으로 변환

        Args:
            event_key: 이벤트 키 문자열

        Returns:
            EventType 또는 None (매칭되는 이벤트가 없는 경우)
        """
        raise NotImplementedError()

    @abstractmethod
    def clear_cache(self) -> None:
        """이벤트 타입 캐시 초기화"""
        raise NotImplementedError()


class ISubscriptionManager(ABC):
    """이벤트 구독 관리를 위한 인터페이스

    특정 이벤트 타입에 해당하는 콜백 함수를 등록하고 관리하는 기능 제공
    """

    @abstractmethod
    async def subscribe(
        self, event_type: EventType | str, callback: CallbackFunction
    ) -> None:
        """특정 이벤트 타입에 콜백 함수 등록

        Args:
            event_type: 구독할 이벤트 타입 (Enum 또는 문자열)
            callback: 이벤트 발생 시 호출될 비동기 콜백 함수
        """
        raise NotImplementedError()

    @abstractmethod
    async def unsubscribe(
        self, event_type: EventType | str, callback: CallbackFunction
    ) -> None:
        """이벤트 타입에서 콜백 함수 등록 해제

        Args:
            event_type: 구독 취소할 이벤트 타입 (Enum 또는 문자열)
            callback: 구독 취소할 콜백 함수
        """
        raise NotImplementedError()

    @abstractmethod
    def get_subscribers(self, event_key: str) -> list[CallbackFunction]:
        """특정 이벤트 타입에 대한 구독자 리스트 반환

        Args:
            event_key: 이벤트 타입 키

        Returns:
            구독자 콜백 함수 리스트
        """
        raise NotImplementedError()

    @abstractmethod
    def clear_subscribers(self) -> None:
        """모든 구독자 정보 제거"""
        raise NotImplementedError()


class IEventStorage(ABC):
    """이벤트 저장소 인터페이스

    이벤트의 저장 및 조회를 담당하는 인터페이스 정의
    메모리, Redis, 데이터베이스 등 다양한 백엔드 구현체 지원
    """

    @abstractmethod
    async def store_event(self, event_key: str, payload: EventPayload) -> None:
        """이벤트 저장

        Args:
            event_key: 이벤트 타입 키
            payload: 저장할 이벤트 페이로드
        """
        raise NotImplementedError()

    @abstractmethod
    async def get_events(
        self, event_key: str, start: Any = None, end: Any = None
    ) -> list[EventPayload]:
        """특정 이벤트 타입의 이벤트 조회

        Args:
            event_key: 이벤트 타입 키
            start: 조회 시작 지점 (백엔드 구현체에 따라 의미가 다를 수 있음)
            end: 조회 종료 지점 (백엔드 구현체에 따라 의미가 다를 수 있음)

        Returns:
            이벤트 페이로드 리스트
        """
        raise NotImplementedError()

    @abstractmethod
    async def clear_events(self, event_key: str | None = None) -> None:
        """이벤트 데이터 삭제

        Args:
            event_key: 삭제할 이벤트 타입 키 (None인 경우 모든 이벤트 삭제)
        """
        raise NotImplementedError()


class IEventBus(ABC):
    """이벤트 버스 인터페이스

    이벤트 발행(publishing)과 구독(subscribing)을 관리하는 중앙 허브 인터페이스.
    다양한 백엔드(메모리, Redis, Kafka 등)에 대한 구현체 지원
    """

    @abstractmethod
    async def start(self) -> None:
        """이벤트 버스 시작"""
        raise NotImplementedError()

    @abstractmethod
    async def stop(self) -> None:
        """이벤트 버스 정지"""
        raise NotImplementedError()

    @abstractmethod
    async def publish(
        self,
        event_type: EventType | str,
        data: Any = None,
        metadata: EventMetadata = None,
    ) -> None:
        """이벤트 발행 및 모든 구독자에게 전파

        Args:
            event_type: 발행할 이벤트 타입 (Enum 또는 문자열)
            data: 이벤트와 함께 전달할 데이터
            metadata: 이벤트 메타데이터 (우선순위, 소스 등 포함)
        """
        raise NotImplementedError()

    @abstractmethod
    async def subscribe(
        self, event_type: EventType | str, callback: CallbackFunction
    ) -> None:
        """특정 이벤트 타입에 콜백 함수 등록

        Args:
            event_type: 구독할 이벤트 타입 (Enum 또는 문자열)
            callback: 이벤트 발생 시 호출될 비동기 콜백 함수
        """
        raise NotImplementedError()

    @abstractmethod
    async def unsubscribe(
        self, event_type: EventType | str, callback: CallbackFunction
    ) -> None:
        """이벤트 타입에서 콜백 함수 등록 해제

        Args:
            event_type: 구독 취소할 이벤트 타입 (Enum 또는 문자열)
            callback: 구독 취소할 콜백 함수
        """
        raise NotImplementedError()
