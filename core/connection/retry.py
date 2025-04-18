import asyncio
from typing import Any
from dataclasses import dataclass

from adapters.base.event.event_bus import EventBus
from adapters.base.event.types.event_types import (
    EventType,
    ConnectionRequestPayload,
    ConnectionRetryPayload,
    ConnectionFailurePayload,
    ConnectionMaxRetryPayload,
    EventMetadata,
)
from common.logger import PipelineLogger
from common.registry import get_exchange

# 파이프라인 로거 설정
connection_logger = PipelineLogger.get_logger("connection", "retryconnection")


@dataclass
class ConnectionRetryService:
    """연결 재시도 기능을 제공하는 서비스 클래스

    이벤트 기반 아키텍처(EDA)에 맞게 구현되어 있어, 개별 함수 호출이 아닌 이벤트 발행/구독을 통해 동작합니다.

    연결 재시도 서비스 초기화

    Args:
        event_bus: 이벤트 버스 인스턴스
        max_retries: 최대 재시도 횟수
        retry_delay: 재시도 지연 시간(초)

    """

    event_bus: EventBus
    max_retries: int = 3
    retry_delay: int = 5

    # 이벤트 핸들러 등록 - 이것은 나중에 비동기적으로 실행되어야 함
    # 현재 인스턴스 생성 시점에서는 비동기 함수 사용이 하드코딩되어 있음
    _retry_wrapper: Any = None
    _failure_wrapper: Any = None

    def __post_init__(self) -> None:
        """이벤트 핸들러 등록"""
        self._register_handlers()

    async def _retry_handler(self, data: ConnectionRetryPayload) -> None:
        """재시도 이벤트 핸들러

        Args:
            data: 재시도 페이로드
        """
        exchange_name = data.get("exchange_name")
        attempt = data.get("attempt")
        error = data.get("error")
        max_retries = data.get("max_retries") or self.max_retries
        retry_delay = self.retry_delay

        connection_logger.set_context(exchange=exchange_name)
        connection_logger.warning(
            f"연결 실패 ({attempt}/{max_retries}): {error}. {retry_delay}초 후 재시도...",
            exchange=exchange_name,
            retry_count=attempt,
            error=error,
        )

        # 재시도 제한 횟수 체크
        if attempt >= max_retries:
            connection_logger.error(
                f"최대 재시도 횟수 초과: {error}",
                exchange=exchange_name,
                max_retries=max_retries,
            )
            # 최대 재시도 횟수 초과 이벤트 발행
            await self.event_bus.publish(
                EventType.CONNECTION_MAX_RETRY,
                ConnectionMaxRetryPayload(
                    exchange_name=exchange_name,
                    max_retries=max_retries,
                    error=error,
                ),
                EventMetadata(source=exchange_name),
            )
            return

        # 재시도 전 지연
        await asyncio.sleep(retry_delay)

        # 재연결 요청
        connection_logger.info(
            f"재연결 시도 ({attempt}/{max_retries})",
            exchange=exchange_name,
            attempt=attempt,
        )

        # 재시도 시 원래 연결 요청 이벤트 다시 발행
        socket_param = get_exchange(exchange_name)
        await self.event_bus.publish(
            EventType.CONNECTION_REQUEST,
            ConnectionRequestPayload(
                exchange_name=exchange_name,
                parameter_info=socket_param["parameter_info"],
                socket_instance=socket_param["socket"],
                retry_count=attempt,
            ),
            EventMetadata(source="connection_retry_service"),
        )

    async def _failure_handler(self, data: ConnectionFailurePayload) -> None:
        """연결 실패 이벤트 핸들러

        Args:
            data: 연결 실패 페이로드
        """
        exchange_name = data.get("exchange_name")
        error = data.get("error")
        retry_count = data.get("retry_count")

        connection_logger.set_context(exchange=exchange_name)
        connection_logger.error(
            f"연결 실패 ({retry_count}회): {error}",
            exchange=exchange_name,
            retry_count=retry_count,
            error=error,
        )

        # 재시도 이벤트 발행
        await self.event_bus.publish(
            EventType.CONNECTION_RETRY,
            ConnectionRetryPayload(
                exchange_name=exchange_name,
                attempt=retry_count + 1,
                error=error,
                max_retries=self.max_retries,
            ),
            EventMetadata(source="connection_retry_service"),
        )

    def _register_handlers(self) -> None:
        """이벤트 핸들러 등록"""

        # 동기 코드에서 비동기 함수를 등록하기 위한 wrapper 함수
        async def retry_wrapper(data: Any) -> None:
            await self._retry_handler(data)

        async def failure_wrapper(data: Any) -> None:
            await self._failure_handler(data)

        # 이벤트 핸들러 등록
        self._retry_wrapper = retry_wrapper
        self._failure_wrapper = failure_wrapper

        # 이벤트 구독 등록 - 이것은 나중에 비동기적으로 실행되어야 함
        # 현재 인스턴스 생성 시점에서는 비동기 함수 사용이 하드코딩되어 있음
        asyncio.create_task(
            self.event_bus.subscribe(EventType.CONNECTION_RETRY, retry_wrapper)
        )
        asyncio.create_task(
            self.event_bus.subscribe(EventType.CONNECTION_FAILURE, failure_wrapper)
        )

        connection_logger.info("연결 재시도 서비스 이벤트 핸들러 등록 완료")

    async def cleanup(self) -> None:
        """서비스 종료 시 이벤트 핸들러 등록 해제

        서비스 종료 시 이벤트 핸들러 등록을 해제하여, 이벤트 버스와의 연결을 끊습니다.
        이벤트 핸들러 등록 해제는 서비스 종료 시에만 호출되어야 합니다.
        """
        # 이벤트 핸들러 등록 해제
        if not self._retry_wrapper or not self._failure_wrapper:
            connection_logger.warning(
                "이벤트 핸들러 등록 해제 실패: 이벤트 핸들러가 등록되지 않았습니다."
            )
            return

        connection_logger.info("연결 재시도 서비스 이벤트 핸들러 등록 해제 중")

        # 이벤트 구독 해제
        await self.event_bus.unsubscribe(
            EventType.CONNECTION_RETRY,
            self._retry_wrapper,
        )
        await self.event_bus.unsubscribe(
            EventType.CONNECTION_FAILURE,
            self._failure_wrapper,
        )
        connection_logger.info("연결 재시도 서비스 이벤트 핸들러 등록 해제 완료")

        # 이벤트 핸들러 초기화
        self._retry_wrapper = None
        self._failure_wrapper = None
