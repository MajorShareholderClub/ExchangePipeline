import aiohttp
from abc import abstractmethod
from typing import Any

from common.exception import RestRetryOnFailure
from common.core.types import ExchangeResponseData
from common.core.abstract import (
    AbstractAsyncRequestAcquisition,
    AbstractExchangeRestClient,
)

# fmt: off
class AsyncRequestAcquisition(AbstractAsyncRequestAcquisition):
    """비동기 HTML 처리 클래스"""

    async def async_response(self, session: aiohttp.ClientSession) -> Any:
        async with session.get(url=self.url, params=self.params, headers=self.headers) as response:
            response.raise_for_status()
            data = await response.json(content_type="application/json")
            return data
        
    async def json_async_source(self) -> Any:
        """호출 시작점"""
        async with aiohttp.ClientSession() as session:
            return await self.async_response(session=session)



class CoinExchangeRestClient(AbstractExchangeRestClient):        
    async def async_request_data(self, url: str) -> ExchangeResponseData:
        """비동기 호출 함수"""
        json_header = {"Accept": "application/json"}
        return await AsyncRequestAcquisition(url=url, headers=json_header).json_async_source()

    @RestRetryOnFailure(retries=3, base_delay=2)        
    async def get_coin_all_info_price(self, coin_name: str) -> ExchangeResponseData:
        """코인데이터 호출"""
        data = await self.async_request_data(url=self._get_ticker_url(coin_name))
        if data is not None:
            return data
        else:
            return None

    @abstractmethod
    def _get_ticker_url(self, coin_name: str) -> str:
        """티커 URL 생성
        
        Args:
            coin_name: 코인 이름
            
        Returns:
            str: 티커 API URL
        """
        pass
