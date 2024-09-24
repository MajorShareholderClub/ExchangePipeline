import json
from pathlib import Path
from typing import NoReturn, ClassVar
from .types import (
    MarketRequestJsonType,
    KoreaExchageRest,
    KoreaExchageSocket,
    KoreaMarketRequestType,
    ForeignExchageRest,
    ForeignMarketRequestType,
    WorldMarket,
    WorldMarketsRequestType,
)
from korea_exchange.rest_korea_exchange import (
    UpbitRest,
    BithumbRest,
    CoinoneRest,
    KorbitRest,
)
from korea_exchange.socket_korea_exchange import (
    UpbitSocket,
    BithumbSocket,
    CoinoneSocket,
)
from foreign_exchange.rest_foreign_exchange import (
    BinanceRest,
    KrakenRest,
    OKXRest,
    CoinbaseRest,
    BybitRest,
    GateIORest,
    HTXRest,
)


class __MarketAPIFactory:
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
                htx=HTXRest,
                coinbase=CoinbaseRest,
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


path = Path(__file__).parent.parent

# fmt: off
RequestDict = dict[str, str | WorldMarket]
def load_json(conn_type: str, c: str) -> RequestDict:
    """
    JSON 파일 로드 (socket 또는 rest)
        - 어떤 가격대를 가지고 올지 파라미터 정의되어 있음
    """
    with open(
        file=f"{path}/config/{c}/_market_{conn_type}.json", mode="r", encoding="utf-8"
    ) as file:
        market_info: MarketRequestJsonType = json.load(file)

    # JSON에 저장되어 있는 값 + API 클래스 주소
    korea_markets: RequestDict = {
        market: {
            **info,
            "api": __MarketAPIFactory.market_load(
                conn_type=conn_type, market=market, c=c
            ),
        }
        for market, info in market_info.items()
    }
    return korea_markets
