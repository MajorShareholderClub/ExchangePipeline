import asyncio
import logging
from functools import wraps
from typing import Callable, Any
from common.utils.logger import AsyncLogger
from aiohttp import ClientConnectorError, ClientError
from aiohttp.web_exceptions import HTTPException
from websockets.exceptions import ConnectionClosedOK, ConnectionClosedError
import websockets


class SocketError(Exception): ...


# 기본적인 재시도 로직을 포함하는 추상 클래스
class BaseRetry:
    def __init__(self, retries=3, delay=2):
        self.retries = retries
        self.delay = delay
        self.logging = AsyncLogger(target="request", log_file="request.log")

    def log_error(self, message: str) -> None:
        """로그 메시지를 기록하는 메서드."""
        self.logging.log_message_sync(logging.ERROR, message=message)

    def __call__(self, func: Callable) -> Callable:
        """데코레이터로 사용하기 위한 메서드."""

        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            for attempt in range(self.retries):
                try:
                    return await func(*args, **kwargs)  # 비동기 함수 호출
                except Exception as e:  # 모든 예외 처리
                    await self.handle_exception(e, attempt)  # 비동기 예외 처리
                    await asyncio.sleep(self.delay)  # 재시도 전 대기
            # 재시도 실패 시 마지막 예외를 raise
            raise e

        return wrapper

    async def handle_exception(self, e: Exception, attempt: int) -> None:
        """예외를 처리하는 메서드. 하위 클래스에서 구현."""
        raise NotImplementedError("Subclasses must implement handle_exception method.")


# HTTP 요청에 대한 재시도 클래스
class RestRetryOnFailure(BaseRetry):
    async def handle_exception(self, e: Exception, attempt: int) -> None:
        match e:
            case HTTPException():
                message = f"HTTP Error: {e} 연결 다시 시작합니다 {attempt + 1}/{self.retries}..."
                self.log_error(message)
            case ClientConnectorError():
                message = f"연결 오류: {e}, 연결 다시 시작합니다 {attempt + 1}/{self.retries}..."
                self.log_error(message)
            case ClientError():
                message = f"Client Error: {e}, 재시도 {attempt + 1}/{self.retries}..."
                self.log_error(message)


class SocketRetryOnFailure(BaseRetry):
    def __init__(
        self,
        symbol: str,
        uri: str,
        rest_client: Callable,
        retries: int = 3,
        delay: int = 2,
    ):
        super().__init__(retries, delay)
        self.rest_client = rest_client  # REST API 클라이언트를 인자
        self.symbol = symbol
        self.is_rest_active = False  # REST API 활성화 상태 추적
        self.uri = uri

    def __call__(self, func: Callable) -> Callable:
        """데코레이터로 재시도 및 오류 감지"""

        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                for attempt in range(self.retries):
                    message = f"""
                        --> Socket Error: {last_exception}, 
                        --> 재시도 {attempt + 1}/{self.retries}...
                    """
                    self.log_error(message)
                    await self.handle_exception(e, attempt)
                    await asyncio.sleep(self.delay)  # 재시도 전 대기
                    if await self.ping_pong():  # 소켓이 복구되었는지 확인
                        self.log_error("소켓 복구 감지, 소켓으로 전환합니다...")
                        break

            # 재시도 실패 시 오류 감지 후 Rest API 전환 트리거
            return await self.on_failure_detected(last_exception)

        return wrapper

    async def ping_pong(self) -> None:
        """주기적으로 핑을 보내는 메서드"""
        try:
            async with websockets.connect(self.uri, ping_interval=60) as websocket:
                a = await websocket.ping("PING")  # 서버에 핑 전송
                self.logging.log_message_sync(logging.INFO, f"Ping sent -- {self.uri}")
                await asyncio.sleep(5)  # 설정한 간격만큼 대기
        except Exception as e:
            self.logging.log_message_sync(
                logging.ERROR, f"Ping 에러: {e} -- {self.uri}"
            )

    async def on_failure_detected(self, e: Exception) -> Any:
        """연결 실패가 감지되면 호출"""
        self.log_error(f"소켓 연결 실패 감지: {e}, Rest API로 전환 중...")
        return await self.switch_to_rest()  # 실패 후 REST API 호출

    async def handle_exception(self, e: Exception, attempt: int) -> None:
        """오류를 감지하고 로그를 남김"""
        match e:
            case TimeoutError() | ConnectionClosedOK() | ConnectionClosedError():
                self.log_error(f"연결 오류 --> {e}")
                asyncio.sleep(1)
            case SocketError():
                message = "연결이 진행되지 않습니다 REST로 대체합니다"
                self.log_error(message)
                await self.switch_to_rest()

    async def switch_to_rest(self) -> Any:
        """모든 재시도가 실패한 후 REST API로 전환"""
        try:
            while True:
                # REST API 요청
                await self.rest_client.total_pull_request(coin_symbol=self.symbol)
                self.log_error(f"Rest API로 전환 성공")

                # 소켓 복구 여부 확인
                if await self.ping_pong():  # 소켓이 복구되었는지 확인
                    self.log_error("소켓 복구 감지, 소켓으로 전환합니다...")
                    break  # REST 루프 종료

                await asyncio.sleep(2)  # REST API 요청 간격 조정
        except Exception as e:
            self.log_error(f"Rest API 요청 중 오류 발생: {e}")
            raise e  # Rest API 호출도 실패하면 예외 처리
