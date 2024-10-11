import yaml
from pathlib import Path
from typing import NoReturn, ClassVar, Callable
from .types import (
    MarketRequestJsonType,
    KoreaExchageRest,
    KoreaExchageSocket,
    KoreaMarketRequestType,
    ForeignExchageRest,
    ForeignExchageSocket,
    ForeignMarketRequestType,
    WorldMarket,
    WorldMarketsRequestType,
)
from korea.client.rest_korea_exchange import (
    UpbitRest,
    BithumbRest,
    CoinoneRest,
    KorbitRest,
)
from korea.client.socket_korea_exchange import (
    UpbitSocket,
    BithumbSocket,
    CoinoneSocket,
    KorbitSocket,
)
from foreign.client.rest_foreign_exchange import (
    BinanceRest,
    KrakenRest,
    OKXRest,
    BybitRest,
    GateIORest,
    CoinbaseRest,
)
from foreign.client.socket_foreign_exchange import (
    KrakenSocket,
    OKXSocket,
    GateIOSocket,
    BinanceSocket,
    ByBitSocket,
    CoinbaseSocket,
)

path = Path(__file__).parent.parent
RequestDict = dict[str, str | WorldMarket]


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
        foreign=ForeignMarketRequestType(
            rest=ForeignExchageRest(
                binance=BinanceRest,
                kraken=KrakenRest,
                okx=OKXRest,
                bybit=BybitRest,
                gateio=GateIORest,
                coinbase=CoinbaseRest,
            ),
            socket=ForeignExchageSocket(
                binance=BinanceSocket,
                kraken=KrakenSocket,
                okx=OKXSocket,
                gateio=GateIOSocket,
                bybit=ByBitSocket,
                coinbase=CoinbaseSocket,
            ),
        ),
    )

    @classmethod
    def market_load(
        cls, conn_type: str, market: str, c: str, *args, **kwargs
    ) -> WorldMarket | NoReturn:
        """
        거래소 API의 인스턴스를 생성합니다.
        """
        if conn_type not in cls._create[c]:
            raise ValueError(f"잘못된 연결 유형: {conn_type}")

        creator = cls._create[c][conn_type][market]
        return creator(*args, **kwargs)


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

    def _market_api_load(self, market: str):
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
