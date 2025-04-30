from __future__ import annotations
from typing import Callable, TypeVar, Union, Any, TypedDict
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import uuid
import time

# 이벤트 데이터 타입
T = TypeVar("T")

"""
콜백 함수 타입 정의
콜백이 두 가지 반환 타입을 가질 수 있음:
  1. None: 일반적인 비동기 함수처럼 반환값 없이 실행
  2. Future[None]: await를 통해 완료를 기다릴 수 있는 비동기 작업을 반환
  이는 다음과 같은 상황에서 유용함:
    - 콜백이 데이터베이스 연산이나 네트워크 요청과 같은 I/O 작업을 수행하는 경우
    - 이벤트 처리가 완료되기를 기다려야 하는 경우
"""
CallbackFunction = Callable[[T], Union[None, asyncio.Future[None]]]

# 구독자 목록 타입 <-- 이벤트 타입별 구독자 맵 타입
SubscribersList = list[CallbackFunction]
SubscribersMap = dict[str, SubscribersList]


class DataPayload(TypedDict):
    """마켓 티커 이벤트 페이로드"""

    region: str
    exchange: str
    request_type: str
    timestamp: float
    data: Any


class ConnectPayload(TypedDict):
    exchange: str
    status: str
    request_type: str


# 연결 관리 관련 이벤트 페이로드
class ConnectionRequestPayload(TypedDict):
    """연결 요청 이벤트"""

    coin_symbol: str
    metadata: dict[str, str]
    parameter_info: dict | list[dict]
    request_type: str
    socket_instance: Any
    retry_count: int


class ConnectionClosePayload(TypedDict):
    """연결 종료 이벤트"""

    exchange_name: str
    reason: str
    request_type: str


class ConnectionSuccessPayload(TypedDict):
    """연결 성공 이벤트"""

    exchange_name: str
    request_type: str


class ConnectionFailurePayload(TypedDict):
    """연결 실패 이벤트"""

    exchange_name: str
    error: str
    retry_count: int
    request_type: str
    parameter_info: dict | None
    socket_instance: Any | None


class ConnectionRetryPayload(TypedDict):
    """연결 재시도 이벤트"""

    exchange_name: str
    attempt: int
    error: str
    max_retries: int
    request_type: str
    parameter_info: dict | None
    socket_instance: Any | None


class ConnectionMaxRetryPayload(TypedDict):
    """최대 재시도 횟수 초과 이벤트"""

    exchange_name: str
    max_retries: int
    error: str
    request_type: str


# fmt: off
class EventType(Enum):
    """이벤트 타입을 정의하는 Enum 클래스

    문자열 대신 Enum을 사용하면 다음과 같은 이점이 있음:
    1. 타입 안전성: IDE에서 자동 완성 및 오타 감지 가능
    2. 리팩토링: 이벤트 타입 이름 변경 시 자동 반영
    3. 그룹화: 관련 이벤트를 계층적으로 구성 가능
    4. 문서화: 각 이벤트 타입에 대한 설명을 Enum에 직접 포함 가능
    """

    # 시스템 이벤트
    SYSTEM_STARTUP = "system.startup"  # 시스템 시작 이벤트
    SYSTEM_SHUTDOWN = "system.shutdown"  # 시스템 종료 이벤트
    SYSTEM_ERROR = "system.error"  # 시스템 오류 이벤트

    # 거래소 연결 관련 이벤트
    EXCHANGE_CONNECT = "exchange.connect"  # 거래소 연결 성공 이벤트
    EXCHANGE_DISCONNECT = "exchange.disconnect"  # 거래소 연결 종료 이벤트
    EXCHANGE_ERROR = "exchange.error"  # 거래소 연결 오류 이벤트
    
    # 연결 관리 관련 이벤트
    CONNECTION_REQUEST = "connection.request"  # 연결 요청 이벤트
    CONNECTION_SUCCESS = "connection.success"  # 연결 성공 이벤트
    CONNECTION_FAILURE = "connection.failure"  # 연결 실패 이벤트
    CONNECTION_RETRY = "connection.retry"  # 연결 재시도 이벤트
    CONNECTION_MAX_RETRY = "connection.max_retry"  # 최대 재시도 횟수 초과 이벤트
    CONNECTION_CLOSE = "connection.close"  # 연결 종료 이벤트

    # 시장 데이터 이벤트
    MARKET_TICKER = "market.ticker"  # 현재가 이벤트
    MARKET_ORDERBOOK = "market.orderbook"  # 호가창 이벤트
    MARKET_TRADE = "market.trade"  # 체결 이벤트
    
    # 배치 데이터 이벤트
    MARKET_BATCH = "market.batch"  # 배치 이벤트

    @classmethod
    def from_string(cls, event_name: str) -> EventType | None:
        """문자열로부터 EventType을 찾아 반환

        이전 버전과의 호환성을 위해 문자열 기반 이벤트 타입도 지원

        Args:
            event_name: 이벤트 타입 문자열

        Returns:
            해당하는 EventType 또는 None (매칭되는 이벤트가 없는 경우)
        """
        for event_type in cls:
            if event_type.value == event_name:
                return event_type
        return None

    def __str__(self) -> str:
        """EventType을 문자열로 변환"""
        return self.value

@dataclass(frozen=True)
class EventBatchConfig:
    """이벤트 배치 처리를 위한 설정 클래스"""

    max_events: int = 100  # 배치 처리 최대 이벤트 수
    timeout: float = 10.0  # 배치 처리 타임아웃 (초)


# 이벤트 메타데이터 타입
@dataclass(frozen=True)
class EventMetadata:
    """이벤트에 대한 추가 정보를 포함하는 메타데이터

    이벤트 식별, 추적, 관리 등에 활용
    """

    source: str = None  # 이벤트 발생 소스 (예: 거래소 이름)
    timestamp: float = field(default_factory=time.time)  # 이벤트 발생 시간 (Unix 타임스탬프)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))  # 이벤트 고유 식별자
    extra: dict[str, Any] = field(default_factory=dict)  # 추가 메타데이터


# 이벤트 페이로드 타입 (데이터 + 메타데이터)
@dataclass(frozen=True)
class EventPayload:
    """이벤트 데이터와 메타데이터를 포함하는 페이로드"""

    data: Any  # 이벤트 데이터
    metadata: EventMetadata = field(default_factory=EventMetadata)  # 이벤트 메타데이터
