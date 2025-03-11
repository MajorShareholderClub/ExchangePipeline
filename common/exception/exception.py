import json
import logging
import random
from abc import ABC, abstractmethod
from functools import wraps
from typing import Callable, Any

import asyncio
from aiohttp import ClientConnectorError, ClientError
from aiohttp.web_exceptions import HTTPException
from asyncio.exceptions import CancelledError, TimeoutError

import websockets
from websockets.exceptions import WebSocketException
from websockets.exceptions import (
    ConnectionClosedOK,
    ConnectionClosedError,
    ConnectionClosed,
)
from common.utils.logger import AsyncLogger


class SocketError(Exception): ...


# 기본적인 재시도 로직을 포함하는 추상 클래스
class BaseRetry(ABC):
    def __init__(self, retries=3, base_delay=2, max_delay=60):
        self.retries = retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.current_retry = 0
        self.logging = AsyncLogger(target="connection", folder="error")

    async def log_error(self, message: str) -> None:
        """비동기로 로그 메시지를 기록하는 메서드."""
        await self.logging.log_message(logging.ERROR, message=message)

    def calculate_delay(self) -> float:
        """지수 백오프를 사용하여 다음 재시도까지의 지연 시간을 계산"""
        delay = min(self.base_delay * (2**self.current_retry), self.max_delay)
        return delay + (random.uniform(0, 0.1) * delay)  # 지터 추가

    async def execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """공통 재시도 로직을 처리하는 메서드"""
        while self.current_retry < self.retries:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                self.current_retry += 1
                if self.current_retry >= self.retries:
                    await self.log_error(
                        f"최대 재시도 횟수({self.retries})에 도달했습니다."
                    )
                    raise

                await self.handle_exception(e)
                delay = self.calculate_delay()
                await self.log_error(
                    f"재시도 {self.current_retry}/{self.retries}, {delay:.2f}초 후 다시 시도합니다."
                )
                await asyncio.sleep(delay)

    @abstractmethod
    async def handle_exception(self, e: Exception) -> None:
        """예외 처리 메서드. 하위 클래스에서 구현."""
        pass

    def __call__(self, func: Callable) -> Callable:
        """데코레이터로 사용"""

        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            return await self.execute_with_retry(func, *args, **kwargs)

        return wrapper


class RestRetryOnFailure(BaseRetry):
    async def handle_exception(self, e: Exception) -> None:
        """HTTP 예외 처리 로직

        Args:
            e: 발생한 예외
        """
        # HTTP 관련 예외 시 적절한 오류 메시지 생성
        if isinstance(e, (HTTPException, ClientConnectorError, ClientError)):
            message = f"Error: {e}. 재시도 진행합니다"
        else:
            message = f"Unknown Error: {e}. 재시도 진행합니다"

        await self.log_error(message)


class SocketRetryOnFailure(BaseRetry):
    def __init__(
        self,
        symbol: str,
        uri: str,
        rest_client: Callable,
        subs: list,
        retries: int = 3,
        base_delay: int = 2,
    ):
        super().__init__(retries, base_delay)
        self.symbol = symbol
        self.uri = uri
        self.subs = subs
        self.rest_client = rest_client

    async def handle_exception(self, e: Exception) -> None:
        """소켓 및 연결 오류 예외 처리

        Args:
            e: 발생한 예외
        """
        # 소켓 연결 관련 예외 목록
        connection_exceptions = (
            TimeoutError,
            ConnectionClosedOK,
            ConnectionClosedError,
            SocketError,
            CancelledError,
            WebSocketException,
            ConnectionClosed,
            ClientConnectorError,
        )

        # 소켓 연결 예외인 경우 단순 재시도 메시지 출력
        if isinstance(e, connection_exceptions):
            message = f"연결 오류: {e}. 재시도 합니다"
            await self.log_error(message)
        # 그 외 예외는 REST API로 전환
        else:
            message = "클라이언트 연결이 끊어졋음으로 RestAPI 로 전환합니다"
            await self.log_error(message)
            await self.switch_to_rest()

    async def switch_to_rest(self) -> None:
        """소켓 실패 시 REST API로 전환 및 복구"""
        await self.log_error("REST API로 전환 중...")
        while True:
            try:
                await self.rest_client.total_pull_request(coin_symbol=self.symbol)
                await self.log_error("REST API 호출 성공")
                if await self.connection_test():
                    await self.log_error("소켓 복구 감지, 소켓으로 전환합니다...")
                    return
            except Exception as e:
                await self.log_error(f"REST API 요청 중 오류 발생: {e}")
                await asyncio.sleep(self.base_delay)

    async def connection_test(self, timeout: float = 30.0) -> bool:
        """소켓 핑 테스트 메서드"""
        try:
            async with websockets.connect(self.uri, ping_interval=60) as websocket:
                await websocket.send(json.dumps(self.subs))
                await self.logging.log_message(
                    logging.INFO, f"connection sent -- {self.uri}"
                )

                async def receive_data():
                    while True:
                        data = await websocket.recv()
                        if isinstance(data, (bytes, str)):
                            await self.logging.log_message(
                                logging.INFO, f"연결 성공: {data}"
                            )
                            return True
                        await asyncio.sleep(1)

                try:
                    return await asyncio.wait_for(receive_data(), timeout=timeout)
                except asyncio.TimeoutError:
                    await self.logging.log_message(
                        logging.ERROR, f"연결 테스트 타임아웃 ({timeout}초)"
                    )
                    return False
        except Exception as e:
            await self.logging.log_message(
                logging.ERROR, f"Ping 에러: {e} -- {self.uri}"
            )
            return False
