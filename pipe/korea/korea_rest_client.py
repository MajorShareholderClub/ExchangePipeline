"""
Coin async present price kafka data streaming 
"""

from common.core.data_format import KoreaCoinMarket
from common.core.types import KoreaCoinMarketData, ExchangeData
from common.client.common_exchange_interface import BaseExchangeRestAPI

from korea_exchange.rest_korea_exchange import UpbitRest

# from coin.core.data_mq.data_interaction import KafkaMessageSender


class KoreaExchangeRestAPI(BaseExchangeRestAPI):
    """한국거래소 API"""

    def __init__(self) -> None:
        super().__init__(location="korea")

    async def fetch_api_response_time(self, coin_symbol: str) -> int:
        api_response = await UpbitRest().get_coin_all_info_price(
            coin_name=coin_symbol.upper()
        )
        return api_response["timestamp"]

    def create_schema(
        self, api_response_time: int, market_result: list[ExchangeData]
    ) -> KoreaCoinMarketData:
        return KoreaCoinMarket(
            timestamp=api_response_time,
            **dict(zip(self.market_env.keys(), market_result)),
        ).model_dump()
