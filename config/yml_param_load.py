# fmt: off

import yaml
from pathlib import Path
from typing import ClassVar, Callable
from common.core.types import Result, Ok, Err

from protocols.client.korea.rest_korea_exchange import (
    UpbitRest, BithumbRest, CoinoneRest, KorbitRest
)
from protocols.client.korea.socket_korea_exchange import (
    UpbitSocket, BithumbSocket, CoinoneSocket, KorbitSocket
)

from protocols.client.ne.rest_ne_exchange import (
    BinanceRest, KrakenRest, CoinbaseRest
)
from protocols.client.ne.socket_ne_exchange import (
    BinanceSocket, KrakenSocket, CoinbaseSocket
)

from protocols.client.asia.rest_asia_exchange import (
    OKXRest, GateIORest, BybitRest
)
from protocols.client.asia.socket_asia_exchange import (
    OKXSocket, GateIOSocket, ByBitSocket
)
from .types import (
    MarketRequestJsonType,
    KoreaExchageRest,
    KoreaExchageSocket,
    KoreaMarketRequestType,
    AsiaExchangeRest,
    AsiaExchangeSocket,
    AsiaMarketRequestType,
    NEExchangeRest,
    NEExchangeSocket,
    NEMarketRequestType,
    WorldMarket,
    WorldMarketsRequestType,
)

path = Path(__file__).parent.parent
RequestDict = dict[str, str | WorldMarket]
ClassAddress = str

class MarketAPIFactory:
    """Factory for market APIs."""

    _create: ClassVar = WorldMarketsRequestType(
        korea=KoreaMarketRequestType(
            rest=KoreaExchageRest(
                upbit=UpbitRest,
                bithumb=BithumbRest,
                korbit=KorbitRest,
                coinone=CoinoneRest,
            ),
            socket=KoreaExchageSocket(
                upbit=UpbitSocket,
                bithumb=BithumbSocket,
                korbit=KorbitSocket,
                coinone=CoinoneSocket,
            ),
        ),
        asia=AsiaMarketRequestType(
            rest=AsiaExchangeRest(
                okx=OKXRest,
                bybit=BybitRest,
                gateio=GateIORest,
            ),
            socket=AsiaExchangeSocket(
                okx=OKXSocket,
                bybit=ByBitSocket,
                gateio=GateIOSocket,
            ),
        ),
        ne=NEMarketRequestType(
            rest=NEExchangeRest(
               binance=BinanceRest,
               kraken=KrakenRest,
               coinbase=CoinbaseRest
            ),
            socket=NEExchangeSocket(
                binance=BinanceSocket,
                kraken=KrakenSocket,
                coinbase=CoinbaseSocket
            ),
        ),
    )

    @classmethod
    def market_load(
        cls, conn_type: str, market: str, c: str, *args, **kwargs
    ) -> Result[str, ClassAddress]:
        """
        거래소 API의 인스턴스를 생성합니다.
        """
        match conn_type:
            case conn_type if conn_type not in cls._create[c]:
                return Err(f"잘못된 연결 유형: {conn_type}").error

            case _:
                creator = cls._create[c][conn_type][market]
                return Ok(creator(*args, **kwargs)).value


class MarketLoadType:
    def __init__(self, conn_type: str, location: str) -> None:
        self.conn_type = conn_type
        self.location = location

    def load_json(self) -> RequestDict:
        """
        JSON 파일 로드 (socket 또는 rest)
            - 어떤 가격대를 가지고 올지 파라미터 정의되어 있음
        """
        yml_path = f"{path}/config/{self.location}/_market_{self.conn_type}.yml"
        with open(file=yml_path, mode="r", encoding="utf-8") as file:
            market_info: MarketRequestJsonType = yaml.safe_load(file)
        
        return market_info

    def _market_api_load(self, market: str) -> Result[str, ClassAddress]:
        return MarketAPIFactory.market_load(
            conn_type=self.conn_type, market=market, c=self.location
        )


class SocketMarketLoader(MarketLoadType):
    def __init__(self, location: str) -> None:
        super().__init__(conn_type="socket", location=location)

    def process_market_info(self) -> dict[str, Callable]:
        return {
            market: {
                "api": self._market_api_load(market),
            }
            for market in self.load_json()
        }


class RestMarketLoader(MarketLoadType):
    def __init__(self, location: str) -> None:
        super().__init__(conn_type="rest", location=location)

    def process_market_info(self) -> dict:
        return {
            market: {**info, "api": self._market_api_load(market)}
            for market, info in self.load_json().items()
        }
