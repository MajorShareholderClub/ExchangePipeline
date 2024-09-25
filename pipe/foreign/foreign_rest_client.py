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

    def create_schema(self, market_result: list[ExchangeData]) -> ForeignCoinMarketData:
        return ForeignCoinMarket(
            **dict(zip(self.market_env.keys(), market_result)),
        ).model_dump()
