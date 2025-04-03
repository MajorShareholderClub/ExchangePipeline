# exchanges/exceptions.py 파일
from functools import wraps
from typing import Any, Callable, TypeVar
import json
import logging
import asyncio

from attr import dataclass

from adapters.base.event.event_bus import EventBus
from adapters.base.event.types import EventType, EventMetadata

from common.logger import PipelineLogger

# 제네릭 타입 정의
T = TypeVar("T")
F = TypeVar("F", bound=Callable[..., Any])
logger = PipelineLogger.get_logger("exchange_exceptions", "exceptions")


@dataclass
class ExchangeException(Exception):
    """거래소 관련 기본 예외 클래스"""

    exchange_name: str
    message: str
    original_exception: Exception | None = None

    def __post_init__(self) -> None:
        super().__init__(f"[{self.exchange_name}] {self.message}")

    def to_dict(self) -> dict[str, Any]:
        """예외 정보를 이벤트 데이터로 변환"""
        result = {
            "exchange": self.exchange_name,
            "error": self.message,
            "error_type": self.__class__.__name__,
        }

        if self.original_exception:
            result["original_error"] = str(self.original_exception)
            result["original_error_type"] = self.original_exception.__class__.__name__

        return result


# fmt: off
# 특화된 예외 클래스들
class ConnectionException(ExchangeException): pass
class ConnectionTimeoutException(ConnectionException): pass
class MessageProcessingException(ExchangeException): pass
class JSONParsingException(MessageProcessingException): pass


# 예외 처리 데코레이터
def handle_exchange_exceptions(
    event_bus_attr: str = "event_bus",
    exchange_name_attr: str = "exchange_name",
    publish_event: bool = True,
    exception_mapping: dict[type[Exception], type[ExchangeException]] = None,
    log_level: int = logging.ERROR,
):
    """
    거래소 관련 예외 처리를 위한 데코레이터

    Args:
        event_bus_attr: 이벤트 버스 객체를 가진 속성 이름
        exchange_name_attr: 거래소 이름을 가진 속성 이름
        publish_event: 예외 발생 시 이벤트 발행 여부
        exception_mapping: 일반 예외와 거래소 예외 간의 매핑
        log_level: 로그 레벨
    """
    # 기본 예외 매핑
    if exception_mapping is None:
        exception_mapping = {
            asyncio.TimeoutError: ConnectionTimeoutException,
            json.JSONDecodeError: JSONParsingException,
        }

    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            # 이벤트 버스와 거래소 이름 가져오기
            event_bus = getattr(self, event_bus_attr)
            exchange_name = getattr(self, exchange_name_attr)

            try:
                return await func(self, *args, **kwargs)

            except ExchangeException as e:
                # 이미 ExchangeException인 경우 그대로 사용
                log_exception(e, log_level)
                if publish_event:
                    await publish_exception_event(event_bus, e)
                return None

            except Exception as e:
                # 매핑된 ExchangeException으로 변환
                exchange_exc = map_exception(e, exchange_name, exception_mapping)
                log_exception(exchange_exc, log_level)
                if publish_event:
                    await publish_exception_event(event_bus, exchange_exc)
                return None

        return wrapper

    return decorator


# 헬퍼 함수들
def map_exception(
    exc: Exception,
    exchange_name: str,
    mapping: dict[type[Exception], type[ExchangeException]],
) -> ExchangeException:
    """일반 예외를 ExchangeException으로 변환"""
    for base_exc, exchange_exc in mapping.items():
        if isinstance(exc, base_exc):
            return exchange_exc(exchange_name, str(exc), exc)

    # 매핑되지 않은 예외는 기본 ExchangeException 사용
    return ExchangeException(exchange_name, f"예상치 못한 오류: {str(exc)}", exc)


def log_exception(exc: ExchangeException, level: int) -> None:
    """예외 로깅"""
    if exc.original_exception and level <= logging.ERROR:
        logger.debug(
            f"원인 예외: {exc.original_exception}", exc_info=exc.original_exception
        )


async def publish_exception_event(event_bus: EventBus, exc: ExchangeException) -> None:
    """예외 이벤트 발행"""
    # 중요도 결정 (일부 예외 유형은 덜 중요할 수 있음)
    is_critical = not isinstance(exc, (JSONParsingException, ConnectionTimeoutException))

    # 이벤트 데이터 준비
    event_data = exc.to_dict()
    event_data["is_critical"] = is_critical

    # 이벤트 발행
    await event_bus.publish(
        EventType.EXCHANGE_ERROR,
        event_data,
        EventMetadata(source=exc.exchange_name, extra={"is_critical": is_critical}),
    )
