from abc import ABC, abstractmethod

import time
import logging

import websockets
import asyncio

from typing import Any
from config.yml_param_load import RestMarketLoader

from common.core.types import ExchangeData, KoreaCoinMarketData
from common.core.data_format import CoinMarketData
from common.utils.logger import AsyncLogger


socket_protocol = websockets.WebSocketClientProtocol

"""
REST -----------------------------------------------------------------------------------------------------------------------------
"""


# rest
async def schema_create(
    market: str,
    time: int | float,
    symbol: str,
    api: Any,
    data: tuple[str],
):
    return CoinMarketData.from_api(
        market=market,
        coin_symbol=symbol,
        time=time,
        api=api,
        data=data,
    ).model_dump()


class CoinPresentPriceClient:

    def __init__(self, location: str) -> None:
        self.market_env = RestMarketLoader(location).process_market_info()
        self.logging = AsyncLogger(target=location, folder="rest")

    async def _transform_and_request(
        self, market: str, time: int | float, symbol: str, api: Any, data: tuple[str]
    ) -> ExchangeData:
        """스키마 변환 함수"""
        api_response = await api.get_coin_all_info_price(coin_name=symbol.upper())
        if api_response is None:
            return await schema_create(
                market=market, time=time, symbol=symbol, api=None, data=data
            )
        return await schema_create(
            market=market, time=time, symbol=symbol, api=api_response, data=data
        )

    async def _trans_schema(self, market: str, symbol: str) -> ExchangeData:
        """스키마 변환 본체"""
        # try:
        market_info = self.market_env[market]
        market_data_architecture = await self._transform_and_request(
            market=f"{market}-{symbol.upper()}",
            symbol=symbol,
            time=int(time.time()),
            api=market_info["api"],
            data=market_info["parameter"],
        )
        return market_data_architecture


class BaseExchangeRestAPI(CoinPresentPriceClient, ABC):
    """기본 거래소 API"""

    def __init__(self, location: str) -> None:
        super().__init__(location=location)

    async def fetch_market_data(self, symbol: str) -> list[ExchangeData | Exception]:
        """시장 데이터 가져오기"""
        tasks = [
            self._trans_schema(market=market, symbol=symbol)
            for market in self.market_env
        ]
        return await asyncio.gather(*tasks, return_exceptions=True)

    @abstractmethod
    def create_schema(self, market_result: list[ExchangeData]) -> Any:
        """스키마 생성 메서드"""
        raise NotImplementedError("메서드 구현 필수 입니다")

    async def _log_market_schema(self, coin_symbol: str) -> None:
        """공통 로깅 함수"""
        market_result = await self.fetch_market_data(coin_symbol)
        schema: KoreaCoinMarketData = self.create_schema(market_result)
        await self.logging.log_message(logging.INFO, message=schema)

        return schema

    @abstractmethod
    async def total_pull_request(self, coin_symbol: str, interval: int = 1) -> None:
        """Rest 시작점"""
        raise NotImplementedError("메서드 구현 필수 입니다")
