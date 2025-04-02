import aiohttp
from abc import abstractmethod

from common.setting.types import ExchangeResponseData
from adapters.base.interface.rest_interfaces import AbstractAsyncRequestAcquisition

JSON_HEADER = {"Accept": "application/json"}
CONTENT_TYPE = "application/json"


# fmt: off
class AsyncRequestAcquisition(AbstractAsyncRequestAcquisition):
    """비동기 HTML 처리 클래스"""

    async def async_get_response(self, session: aiohttp.ClientSession) -> ExchangeResponseData:
        async with session.get(url=self.url, params=self.params, headers=self.headers) as response:
            data = await response.json(content_type=CONTENT_TYPE)
            response.raise_for_status()
            return data

    async def json_session_async_source(self) -> ExchangeResponseData:
        """호출 시작점"""
        async with aiohttp.ClientSession() as session:
            return await self.async_get_response(session=session)


class CoinExchangeRestClient:        
    async def async_request_data(self, url: str) -> ExchangeResponseData:
        """비동기 호출 함수"""
        return await AsyncRequestAcquisition(url=url, headers=JSON_HEADER).json_session_async_source()

    @RestRetryOnFailure(retries=3, base_delay=2)        
    async def get_coin_all_info_price(self, coin_name: str) -> ExchangeResponseData:
        """코인데이터 호출"""
        url: str = self._get_ticker_url(coin_name)
        data = await self.async_request_data(url=url)
        return data

    @abstractmethod
    def _get_ticker_url(self, coin_name: str) -> str:
        """티커 URL 생성
        
        Args:
            coin_name: 코인 이름
            
        Returns:
            str: 티커 API URL
        """
        raise NotImplementedError()
