"""
Coin async present price kafka data streaming 
"""

import asyncio
from common.core.data_format import ForeignCoinMarket
from common.core.types import ForeignCoinMarketData, ExchangeData
from common.client.common_exchange_interface import BaseExchangeRestAPI
from mq.data_interaction import KafkaMessageSender


class ForeignExchangeRestAPI(BaseExchangeRestAPI):
    """해외거래소 API"""

    def __init__(self) -> None:
        super().__init__(location="foreign")

    def create_schema(self, market_result: list[ExchangeData]) -> ForeignCoinMarketData:
        return ForeignCoinMarket(
            **dict(zip(self.market_env.keys(), market_result)),
        ).model_dump()

    async def total_pull_request(self, coin_symbol: str, interval: int = 1) -> None:
        i = 0
        while True:
            message = await self._log_market_schema(coin_symbol)
            await KafkaMessageSender().produce_sending(
                message=message,
                market_name="Total",
                symbol=coin_symbol,
                type_="RestDataIn",
                key="Foreign-Total",
            )
            i += 1

            await asyncio.sleep(interval)  # 1초 대기
            if i >= 100:
                print("100번 호출 후 10초 대기합니다.")
                await asyncio.sleep(10)  # 10초 대기
                i = 0  # 카운터 초기화
