from abc import abstractmethod

import time
import logging

import websockets
import asyncio

from typing import Any
from config.yml_param_load import RestMarketLoader

from common.core.types import ExchangeData, CoinDataInfo
from common.core.data_format import CoinMarketData
from common.utils.logger import AsyncLogger
from pipeline.source.rest.async_api_client import CoinExchangeRestClient


socket_protocol = websockets.WebSocketClientProtocol


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
        self._logger = AsyncLogger(target=location, folder="rest")

    async def _transform_and_request(self, coin_data: CoinDataInfo) -> ExchangeData:
        """스키마 변환 함수"""
        api_response = await CoinExchangeRestClient.get_coin_all_info_price(
            coin_name=coin_data.symbol.upper()
        )
        return await schema_create(
            market=coin_data.market,
            time=coin_data.timestamp,
            symbol=coin_data.symbol,
            api=api_response if api_response is not None else None,
            data=coin_data.data,
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


class BaseExchangeRestAPI(CoinPresentPriceClient):
    """기본 거래소 API"""

    async def fetch_market_data(self, symbol: str) -> list[ExchangeData | Exception]:
        """시장 데이터 가져오기"""
        tasks = [
            self._trans_schema(market=market, symbol=symbol)
            for market in self.market_env
        ]
        return await asyncio.gather(*tasks, return_exceptions=True)

    @abstractmethod
    def create_schema(self, market_result: list[ExchangeData]) -> dict: ...

    async def _log_market_schema(self, coin_symbol: str) -> None:
        """공통 로깅 함수"""
        market_result = await self.fetch_market_data(coin_symbol)
        schema = self.create_schema(market_result)
        await self._logger.log_message(logging.INFO, message=schema)

        return schema
