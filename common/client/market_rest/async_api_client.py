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
        
    async def async_source(self) -> Any:
        """호출 시작점"""
        async with aiohttp.ClientSession() as session:
            return await self.async_response(session=session)


class AsyncRequestJSON(AsyncRequestAcquisition):
    """JSON 데이터 호출"""

    async def async_fetch_json(self) -> Any:
        """URL에서 JSON 데이터를 비동기로 가져옴"""
        return await self.async_source()


class CoinExchangeRestClient(AbstractExchangeRestClient):        
    @RestRetryOnFailure(retries=3, base_delay=2)        
    async def get_coin_all_info_price(self, coin_name: str) -> ExchangeResponseData:
        """코인데이터 호출"""
        data = async_request_data(url=self._get_ticker_url(coin_name))
        if data is not None:
            return await data
        else:
            return None

    # @abstractmethod
    # def _get_orderbook_url(self, coin_name: str) -> str:
    #     """ordering 주소"""
    #     pass

    @abstractmethod
    def _get_ticker_url(self, coin_name: str) -> str:
        """ticker 주소"""
        pass



async def async_request_data(url: str) -> ExchangeResponseData:
    """비동기 호출 함수"""
    return await AsyncRequestJSON(
        url=url, headers={"Accept": "application/json"}
    ).async_fetch_json()
