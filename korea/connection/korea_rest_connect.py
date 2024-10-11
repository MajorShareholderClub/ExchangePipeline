"""
Coin async present price kafka data streaming 
"""

import asyncio
from common.core.data_format import KoreaCoinMarket
from common.core.types import KoreaCoinMarketData, ExchangeData
from common.client.market_rest.rest_interface import BaseExchangeRestAPI
from mq.data_interaction import KafkaMessageSender
from mq.data_partitional import CoinHashingCustomPartitional


class KoreaExchangeRestAPI(BaseExchangeRestAPI):
    """한국거래소 API"""

    def __init__(self) -> None:
        super().__init__(location="korea")

    def create_schema(self, market_result: list[ExchangeData]) -> KoreaCoinMarketData:
        return KoreaCoinMarket(
            **dict(zip(self.market_env.keys(), market_result)),
        ).model_dump()

    async def total_pull_request(self, coin_symbol: str, interval: int = 1) -> None:
        i = 0
        while True:
            message = await self._log_market_schema(coin_symbol)
            await asyncio.sleep(interval)
            await KafkaMessageSender(
                partition_pol=CoinHashingCustomPartitional()
            ).produce_sending(
                message=message,
                market_name="Total",
                symbol=coin_symbol,
                type_="RestDataIn",
                request_type="rest",
                key="Korea-Total",
            )
            i += 1

            await asyncio.sleep(interval)  # 1초 대기
            if i >= 100:
                print("100번 호출 후 10초 대기합니다.")
                await asyncio.sleep(10)  # 10초 대기
                i = 0  # 카운터 초기화
