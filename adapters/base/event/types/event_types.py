from __future__ import annotations
from typing import Callable, TypeVar, Union, Any
from enum import Enum
import asyncio
from dataclasses import dataclass, field
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

# 예상되는 비동기 예외 타입
AsyncException: tuple[type[Exception], ...] = (
    asyncio.CancelledError,  # 태스크 취소시 발생
    asyncio.TimeoutError,  # 작업 타임아웃시 발생
    ValueError,  # 데이터 값 관련 오류
    TypeError,  # 데이터 타입 관련 오류
    KeyError,  # 데이터 구조 키 접근 오류
    AttributeError,  # 객체 속성 접근 오류
)


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

    # 시장 데이터 이벤트
    MARKET_TICKER = "market.ticker"  # 현재가 이벤트
    MARKET_ORDERBOOK = "market.orderbook"  # 호가창 이벤트
    MARKET_TRADE = "market.trade"  # 체결 이벤트

    # 주문 관련 이벤트
    ORDER_CREATED = "order.created"  # 주문 생성 이벤트
    ORDER_FILLED = "order.filled"  # 주문 체결 이벤트
    ORDER_CANCELED = "order.canceled"  # 주문 취소 이벤트
    ORDER_REJECTED = "order.rejected"  # 주문 거부 이벤트

    # 기타 사용자 정의 이벤트는 필요에 따라 추가

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


# 이벤트 우선순위 정의
class EventPriority(Enum):
    """이벤트 처리 우선순위

    처리 지연이 발생할 경우 우선순위에 따라 이벤트 처리 순서 결정
    """

    HIGH = 0  # 최우선 처리 (예: 시스템 오류, 주요 알림)
    MEDIUM = 5  # 표준 우선순위 (예: 일반 시장 데이터)
    LOW = 10  # 낮은 우선순위 (예: 로깅, 통계 데이터)


# 이벤트 배치 처리를 위한 설정 타입
@dataclass
class EventBatchConfig:
    """대량의 이벤트 처리 시 배치 처리를 위한 설정

    40개 이상의 거래소에서 동시에 이벤트가 발생할 경우 부하를 관리하기 위한 설정
    """

    batch_size: int = 100  # 한 번에 처리할 최대 이벤트 수
    flush_interval: float = 0.1  # 배치 처리 실행 주기 (초 단위)
    max_queue_size: int = 10000  # 최대 큐 크기 (메모리 사용량 제한)


# 이벤트 메타데이터 타입
@dataclass
class EventMetadata:
    """이벤트에 대한 추가 정보를 포함하는 메타데이터

    이벤트 식별, 추적, 우선순위 관리 등에 활용
    """

    priority: EventPriority = EventPriority.MEDIUM  # 이벤트 처리 우선순위
    source: str = None  # 이벤트 발생 소스 (예: 거래소 이름)
    timestamp: float = field(default_factory=time.time)  # 이벤트 발생 시간 (Unix 타임스탬프)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))  # 이벤트 고유 식별자
    extra: dict[str, Any] = field(default_factory=dict)  # 추가 메타데이터


# 이벤트 페이로드 타입 (데이터 + 메타데이터)
@dataclass
class EventPayload:
    """이벤트 데이터와 메타데이터를 포함하는 페이로드"""

    data: Any  # 이벤트 데이터
    metadata: EventMetadata = field(default_factory=EventMetadata)  # 이벤트 메타데이터
