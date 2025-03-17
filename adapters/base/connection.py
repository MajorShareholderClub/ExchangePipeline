from abc import ABC, abstractmethod
from typing import TypeVar, Generic
import logging
import asyncio
import websockets

T = TypeVar("T")  # 연결 타입
exceptions_to_catch = (
    asyncio.TimeoutError,
    websockets.ConnectionClosed,
    websockets.InvalidMessage,
    websockets.InvalidState,
)


class ConnectionManager(ABC, Generic[T]):
    """연결 관리를 위한 추상 기본 클래스"""

    def __init__(self, logger: logging.Logger | None = None):
        self.logger = logger or logging.getLogger(self.__class__.__name__)

    @abstractmethod
    async def connect(self, **kwargs) -> T:
        """연결 수립 메서드"""
        pass

    @abstractmethod
    async def disconnect(self, connection: T) -> None:
        """연결 종료 메서드"""
        pass

    @abstractmethod
    async def is_connected(self, connection: T) -> bool:
        """연결 상태 확인 메서드"""
        pass

    async def reconnect(self, connection: T, **kwargs) -> T:
        """재연결 메서드"""
        try:
            await self.disconnect(connection)
        except exceptions_to_catch as e:
            self.logger.warning(f"연결 종료 중 오류 발생: {e}")

        return await self.connect(**kwargs)
