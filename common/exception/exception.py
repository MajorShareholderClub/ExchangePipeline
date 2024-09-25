import asyncio
import logging
from functools import wraps
from typing import Callable, Any
from common.utils.logger import AsyncLogger
from aiohttp import ClientConnectorError, ClientError
from aiohttp.web_exceptions import HTTPException
from websockets.exceptions import ConnectionClosedOK, ConnectionClosedError
import websockets
import json
from socket import gaierror


class SocketError(Exception): ...


# 기본적인 재시도 로직을 포함하는 추상 클래스
class BaseRetry:
    def __init__(self, retries=3, base_delay=2):
        self.retries = retries
        self.base_delay = base_delay  # 지수 백오프를 위한 기본 대기 시간
        self.logging = AsyncLogger(target="request", log_file="request.log")

    async def log_error(self, message: str) -> None:
        """비동기로 로그 메시지를 기록하는 메서드."""
        self.logging.log_message_sync(logging.ERROR, message=message)

    def __call__(self, func: Callable) -> Callable:
        """데코레이터로 사용하기 위한 메서드."""

        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            for attempt in range(self.retries):
                try:
                    return await func(*args, **kwargs)  # 비동기 함수 호출
                except Exception as e:
                    await self.handle_exception(e, attempt)
                    await asyncio.sleep(self.base_delay * (2**attempt))  # 지수 백오프
            raise e  # 재시도 실패 시 마지막 예외를 raise

        return wrapper

    async def handle_exception(self, e: Exception, attempt: int) -> None:
        """예외를 처리하는 메서드. 하위 클래스에서 구현."""
        raise NotImplementedError("Subclasses must implement handle_exception method.")


# HTTP 요청에 대한 재시도 클래스
class RestRetryOnFailure(BaseRetry):
    async def handle_exception(self, e: Exception, attempt: int) -> None:
        """HTTP 관련 예외 처리 로직"""
        match e:
            case HTTPException():
                message = f"HTTP Error: {e}. 재시도 {attempt + 1}/{self.retries}..."
            case ClientConnectorError():
                message = f"연결 오류: {e}. 재시도 {attempt + 1}/{self.retries}..."
            case ClientError():
                message = f"Client Error: {e}. 재시도 {attempt + 1}/{self.retries}..."
            case _:
                message = f"Unknown Error: {e}. 재시도 {attempt + 1}/{self.retries}..."
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
        self.rest_client = rest_client
        self.symbol = symbol
        self.is_rest_active = False
        self.uri = uri
        self.subs = subs

    def __call__(self, func: Callable) -> Callable:
        """데코레이터로 재시도 및 오류 감지"""

        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            for attempt in range(self.retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    await self.handle_exception(e, attempt, func, *args, **kwargs)
                    ping_test = await self.ping_pong()
                    if ping_test:
                        await self.log_error("소켓 복구 감지, 소켓으로 전환합니다...")
                        return await func(*args, **kwargs)  # 복구 후 원래 작업 재개
                    await asyncio.sleep(self.base_delay * (2**attempt))  # 지수 백오프

        return wrapper

    async def ping_pong(self) -> bool:
        """소켓 핑 테스트 메서드"""
        try:
            async with websockets.connect(self.uri, ping_interval=60) as websocket:
                await websocket.send(json.dumps(self.subs))  # 서버에 핑 전송
                self.logging.log_message_sync(logging.INFO, f"Ping sent -- {self.uri}")
                await asyncio.sleep(5)  # 설정한 간격만큼 대기
                data = await websocket.recv()
                return isinstance(data, (bytes, str))  # 응답 타입 확인
        except Exception as e:
            self.logging.log_message_sync(
                logging.ERROR, f"Ping 에러: {e} -- {self.uri}"
            )
            return False

    async def handle_exception(
        self, e: Exception, attempt: int, func: Callable, *args, **kwargs
    ) -> None:
        """소켓 및 연결 오류 예외 처리"""
        match e:
            case TimeoutError() | ConnectionClosedOK() | ConnectionClosedError():
                message = f"연결 오류: {e}. 재시도 {attempt + 1}/{self.retries}..."
            case SocketError():
                message = "소켓 연결 오류. REST API로 전환합니다."
                await self.switch_to_rest(func, *args, **kwargs)
            case _:
                message = "모든 연결 오류로. REST API로 전환합니다."
                await self.log_error(message)
                await self.switch_to_rest(func, *args, **kwargs)

    async def switch_to_rest(self, func: Callable, *args, **kwargs) -> Any:
        """소켓 실패 시 REST API로 전환 및 복구 후 소켓으로 전환"""
        await self.log_error("REST API로 전환 중...")
        while True:
            try:
                # REST API 요청
                await self.rest_client.total_pull_request(coin_symbol=self.symbol)
                await self.log_error(f"REST API 호출 성공")

                # 소켓 복구 여부 확인
                if await self.ping_pong():
                    await self.log_error("소켓 복구 감지, 소켓으로 전환합니다...")
                    return await func(*args, **kwargs)  # 복구 후 원래 작업 재개

                await asyncio.sleep(self.base_delay)
            except Exception as e:
                await self.log_error(f"REST API 요청 중 오류 발생: {e}")
                continue
