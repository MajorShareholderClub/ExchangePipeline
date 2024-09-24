from typing import TypedDict, NewType, TypeVar, Union
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


"""
----------------------
|   거래소 dictionary  |
----------------------
"""
# fmt: off
class KoreaExchageRest(TypedDict):
    upbit: UpbitRest
    bithumb: BithumbRest
    korbit: KorbitRest
    coinone: CoinoneRest


class KoreaExchageSocket(TypedDict):
    upbit: UpbitSocket
    bithumb: BithumbSocket
    coinone: CoinoneSocket


class KoreaMarketRequestType(TypedDict):
    rest: KoreaExchageRest
    socket: KoreaExchageSocket


class ForeignExchageRest(TypedDict):
    binance: BinanceRest
    kraken: KrakenRest
    okx: OKXRest
    bybit: BybitRest
    gateio: GateIORest
    htx: HTXRest
    coinbase: CoinbaseRest


class ForeignMarketRequestType(TypedDict):
    rest: ForeignExchageRest


class WorldMarketsRequestType(TypedDict):
    korea: KoreaMarketRequestType
    foreign: ForeignExchageRest


ForeginMarkets = ForeignExchageRest
KoreaMarkets = KoreaExchageRest | KoreaExchageSocket
WorldMarket = ForeginMarkets | KoreaMarkets


"""
--------
| JSON |
--------
"""
# fmt: off
TIMESTAMP = NewType("TIMESTAMP", int)
class SocketJsonType(TypedDict):
    timestamp: TIMESTAMP
    parameter: list[str]

class RestJsonType(TypedDict):
    parameter: list[str]

T = TypeVar("T", bound= Union[SocketJsonType, RestJsonType])
class MarketRequestJsonType(TypedDict):
    market: T


KoreaMarketsLoadJson = MarketRequestJsonType
