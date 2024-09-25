import aiohttp
from typing import Any

from common.core.abstract import AbstractAsyncRequestAcquisition

# fmt: off
class AsyncRequestAcquisition(AbstractAsyncRequestAcquisition):
    """비동기 HTML 처리 클래스"""

    async def async_response(self, session: aiohttp.ClientSession) -> Any:
        async with session.get(url=self.url, params=self.params, headers=self.headers) as response:
            response.raise_for_status()
            data = await response.json(content_type="application/json")
            return data
        
    async def async_source(self) -> Any:
        """호출 시작점"""
        async with aiohttp.ClientSession() as session:
            return await self.async_response(session=session)


class AsyncRequestJSON(AsyncRequestAcquisition):
    """JSON 데이터 호출"""

    async def async_fetch_json(self) -> Any:
        """URL에서 JSON 데이터를 비동기로 가져옴"""
        return await self.async_source()
