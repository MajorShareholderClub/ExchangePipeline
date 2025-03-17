from typing import Type, Callable, Any
import asyncio
import functools
import logging


# 어댑터 기본 예외 클래스
class AdapterError(Exception): ...


# 연결 관련 예외
class ConnectionError(AdapterError): ...


# 데이터 처리 관련 예외
class DataProcessingError(AdapterError): ...


def retry_on_failure(retries: int = 3, base_delay: float = 1.0):
    """실패 시 재시도 데코레이터

    REST와 WebSocket 모두에서 사용할 수 있는 공통 재시도 로직
    """

    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    delay = base_delay * (2**attempt)  # 지수 백오프
                    logging.warning(
                        f"시도 {attempt+1}/{retries} 실패: {e}. {delay}초 후 재시도..."
                    )
                    await asyncio.sleep(delay)
            raise last_exception

        return wrapper

    return decorator
