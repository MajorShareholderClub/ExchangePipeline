from abc import ABC, abstractmethod

import aiohttp
from typing import Any


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
    async def async_response(self, session: aiohttp.ClientSession) -> Any: 
        raise NotImplementedError()
    
    @abstractmethod
    async def json_async_source(self) -> Any:
        raise NotImplementedError()
