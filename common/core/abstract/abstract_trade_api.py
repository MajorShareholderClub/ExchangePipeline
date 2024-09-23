"""대한민국 거래소 그리고 해외거래소 통합 추상 클래스"""

import ccxt
from abc import abstractmethod, ABC
from common.core.types import ExchangeResponseData


# Rest
class AbstractExchangeRestClient(ABC):
    @abstractmethod
    async def get_coin_all_info_price(self, coin_name: str) -> ExchangeResponseData:
        """
        Subject:
            - 코인 인덱스 가격 정보 \n
        Parameter:
            - coin_name (str) : 코인이름\n
        Returns:
            - market 형식
        """
        raise NotImplementedError()


class CommonForeignMarketRestClient(AbstractExchangeRestClient):
    @abstractmethod
    def get_exchange_instance(self) -> ccxt.binance:
        """각 거래소 인스턴스를 반환하는 메서드. 각 하위 클래스가 구현해야 함."""
        raise NotImplementedError()

    @abstractmethod
    def get_symbol(self, coin_name: str) -> str:
        """코인 심볼을 각 거래소에 맞게 변환하는 메서드."""
        raise NotImplementedError()

    async def get_coin_all_info_price(self, coin_name: str) -> ExchangeResponseData:
        markets = self.get_exchange_instance()
        coin: str = self.get_symbol(coin_name=coin_name)
        return markets.fetch_ticker(coin)


# Socket
class AbstractExchangeSocketClient(ABC):
    @abstractmethod
    async def get_present_websocket(self, symbol: str) -> None:
        """
        Subject:
            - 코인 현재가 실시간 \n
        Args:
            - uri (str): 소켓주소
            - subscribe_fmt (list[dict]): 인증파라미터 \n
            - symbol (str) : 심볼
        Returns:
            - 무한루프 \n
        """
        raise NotImplementedError()


{
    "symbol": "BTC/USDT",
    "timestamp": None,
    "datetime": None,
    "high": 64733.2,
    "low": 62370.9,
    "bid": 63576.4,
    "bidVolume": None,
    "ask": 63576.5,
    "askVolume": None,
    "vwap": 63486.64602153746,
    "open": None,
    "close": 63576.4,
    "last": 63576.4,
    "previousClose": None,
    "change": None,
    "percentage": 1.03,
    "average": None,
    "baseVolume": 2427.491658754,
    "quoteVolume": 154113303.65955,
    "info": {
        "currency_pair": "BTC_USDT",
        "last": "63576.4",
        "lowest_ask": "63576.5",
        "highest_bid": "63576.4",
        "change_percentage": "1.03",
        "base_volume": "2427.491658754",
        "quote_volume": "154113303.65955",
        "high_24h": "64733.2",
        "low_24h": "62370.9",
    },
}
