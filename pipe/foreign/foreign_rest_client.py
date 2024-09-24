"""
Coin async present price kafka data streaming 
"""

from common.core.data_format import ForeignCoinMarket
from common.core.types import ForeignCoinMarketData, ExchangeData
from common.client.common_exchange_interface import BaseExchangeRestAPI
from foreign_exchange.rest_foreign_exchange import BinanceRest


class ForeignExchangeRestAPI(BaseExchangeRestAPI):
    """해외거래소 API"""

    def __init__(self) -> None:
        super().__init__(location="foreign")

    async def fetch_api_response_time(self, coin_symbol: str) -> int:
        api_response_time = await BinanceRest().get_coin_all_info_price(
            coin_name=coin_symbol.upper()
        )
        return api_response_time["timestamp"]

    def create_schema(
        self, api_response_time: int, market_result: list[ExchangeData]
    ) -> ForeignCoinMarketData:
        return ForeignCoinMarket(
            timestamp=api_response_time,
            **dict(zip(self.market_env.keys(), market_result)),
        ).model_dump()
