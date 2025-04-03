import asyncio
import logging
from typing import override

from adapters.base.event.types import AsyncException
from adapters.exchange import WorldWebSocket
from common.logger import PipelineLogger

# 파이프라인 로거 설정
connection_logger = PipelineLogger.get_logger("connection", "decorator")


class ConnectionDecorator:
    """연결 관리를 추상화하기 위한 기본 데코레이터 클래스"""

    def __init__(self, connection_manager: WorldWebSocket) -> None:
        self.connection_manager = connection_manager

    async def connect_and_subscribe(self, url: str) -> None:
        return await self.connection_manager.connect_and_subscribe(url)


class RetryConnectionDecorator(ConnectionDecorator):
    """연결 재시도 기능을 추가하는 데코레이터"""

    def __init__(
        self,
        connection_manager: WorldWebSocket,
        max_retries: int = 3,
        retry_delay: int = 5,
        exchange_name: str = "unknown",
    ) -> None:
        super().__init__(connection_manager)
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.exchange_name = exchange_name

        # 로깅을 위한 컨텍스트 설정
        connection_logger.set_context(exchange=exchange_name)

    @override
    async def connect_and_subscribe(self, url: str) -> None:
        retries = 0
        while retries < self.max_retries:
            try:
                connection_logger.info(
                    f"연결 시도",
                    exchange=self.exchange_name,
                    url=url,
                    attempt=retries + 1,
                )
                result = await self.connection_manager.connect_and_subscribe(url)
                connection_logger.info(f"연결 성공", exchange=self.exchange_name)
                return result
            except AsyncException as e:
                retries += 1
                connection_logger.warning(
                    f"연결 실패 ({retries}/{self.max_retries}): {str(e)}. {self.retry_delay}초 후 재시도...",
                    exchange=self.exchange_name,
                    retry_count=retries,
                    error=str(e),
                )
                if retries >= self.max_retries:
                    connection_logger.error(
                        f"최대 재시도 횟수 초과: {str(e)}",
                        exchange=self.exchange_name,
                        max_retries=self.max_retries,
                    )
                    raise
                await asyncio.sleep(self.retry_delay)
