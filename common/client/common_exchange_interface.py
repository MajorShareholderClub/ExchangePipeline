from abc import ABC, abstractmethod

import logging
import asyncio

from typing import Any
from config.json_param_load import load_json
from common.core.types import ExchangeData
from common.core.data_format import CoinMarketData
from common.utils.logger import AsyncLogger

from pydantic.errors import PydanticUserError
from pydantic import ValidationError


class CoinPresentPriceClient:

    def __init__(self, location: str) -> None:
        self.market_env = load_json("rest", location)
        self.logging = AsyncLogger(
            target=f"{location}_rest", log_file=f"{location}_rest.log"
        )

    async def _transform(
        self, market: str, symbol: str, api: Any, data: tuple[str]
    ) -> ExchangeData:
        """스키마 변환 함수"""
        api_response = await api.get_coin_all_info_price(coin_name=symbol.upper())
        return CoinMarketData.from_api(
            market=market,
            coin_symbol=symbol,
            api=api_response,
            data=data,
        ).model_dump()

    async def _trans_schema(self, market: str, symbol: str) -> ExchangeData:
        """스키마 변환 본체"""
        try:
            market_info = self.market_env[market]
            market_data_architecture = await self._transform(
                market=f"{market}-{symbol.upper()}",
                symbol=symbol,
                api=market_info["api"],
                data=market_info["parameter"],
            )
            return market_data_architecture
        except (PydanticUserError, ValidationError) as error:
            self.logging.log_message_sync(logging.ERROR, error)


class BaseExchangeRestAPI(CoinPresentPriceClient, ABC):
    """기본 거래소 API"""

    def __init__(self, location: str) -> None:
        super().__init__(location=location)

    @abstractmethod
    async def fetch_api_response_time(self, coin_symbol: str) -> int:
        """API 응답 시간 가져오기"""
        raise NotImplementedError("메서드 구현 필수 입니다")

    async def fetch_market_data(self, coin_symbol: str) -> list[ExchangeData]:
        """시장 데이터 가져오기"""
        tasks = [
            self._trans_schema(market=market, symbol=coin_symbol)
            for market in self.market_env
        ]
        return await asyncio.gather(*tasks, return_exceptions=True)

    @abstractmethod
    def create_schema(
        self, api_response_time: int, market_result: list[ExchangeData]
    ) -> Any:
        """스키마 생성 메서드"""
        raise NotImplementedError("메서드 구현 필수 입니다")

    async def total_pull_request(self, coin_symbol: str) -> None:
        """시작점"""
        while True:
            try:
                api_response_time = await self.fetch_api_response_time(coin_symbol)
                await asyncio.sleep(1)

                market_result = await self.fetch_market_data(coin_symbol)

                schema = self.create_schema(api_response_time, market_result)
                self.logging.log_message_sync(logging.INFO, message=schema)
            except Exception as error:
                self.logging.log_message_sync(
                    logging.ERROR, f"데이터 변환에 실패했습니다: {error}"
                )
                continue
