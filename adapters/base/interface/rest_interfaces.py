from __future__ import annotations
from abc import ABC, abstractmethod

from common.setting.types import ExchangeResponseData
import aiohttp

# fmt: off
class AbstractAsyncRequestAcquisition(ABC):
    """비동기 호출의 추상 클래스"""

    def __init__(
        self, 
        url: str, 
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.url = url
        self.params = params
        self.headers = headers

    @abstractmethod
    async def async_get_response(self, session: aiohttp.ClientSession) -> ExchangeResponseData: 
        raise NotImplementedError()
    
    @abstractmethod
    async def json_session_async_source(self) -> ExchangeResponseData:
        raise NotImplementedError()
