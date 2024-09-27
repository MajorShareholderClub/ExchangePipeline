from typing import TypedDict, NewType, TypeVar, Union
from common.core.types import ExchangeResponseData


korea_rest = dict
"""
----------------------
|   거래소 dictionary  |
----------------------
"""
# fmt: off
class KoreaExchageRest(TypedDict):
    upbit: ExchangeResponseData
    bithumb: ExchangeResponseData
    korbit: ExchangeResponseData
    coinone: ExchangeResponseData


class KoreaExchageSocket(TypedDict):
    upbit: ExchangeResponseData
    bithumb: ExchangeResponseData
    coinone: ExchangeResponseData


class KoreaMarketRequestType(TypedDict):
    rest: KoreaExchageRest
    socket: KoreaExchageSocket


class ForeignExchageRest(TypedDict):
    binance: ExchangeResponseData
    kraken: ExchangeResponseData
    okx: ExchangeResponseData
    bybit: ExchangeResponseData
    gateio: ExchangeResponseData

class ForeignExchageSocket(TypedDict):
    binance: ExchangeResponseData
    kraken: ExchangeResponseData
    okx: ExchangeResponseData
    bybit: ExchangeResponseData
    gateio: ExchangeResponseData



class ForeignMarketRequestType(TypedDict):
    rest: ForeignExchageRest
    socket: ForeignExchageSocket


class WorldMarketsRequestType(TypedDict):
    korea: KoreaMarketRequestType
    foreign: ForeignMarketRequestType


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
