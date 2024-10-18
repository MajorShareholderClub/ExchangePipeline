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
    korbit: ExchangeResponseData
    coinone: ExchangeResponseData


class KoreaMarketRequestType(TypedDict):
    rest: KoreaExchageRest
    socket: KoreaExchageSocket


# NE 지역 거래소
class NEExchangeRest(TypedDict):
    binance: ExchangeResponseData
    kraken: ExchangeResponseData
    coinbase: ExchangeResponseData

class NEExchangeSocket(TypedDict):
    binance: ExchangeResponseData
    kraken: ExchangeResponseData
    coinbase: ExchangeResponseData


class NEMarketRequestType(TypedDict):
    rest: NEExchangeRest
    socket: NEExchangeSocket


# Asia 지역 거래소
class AsiaExchangeRest(TypedDict):
    okx: ExchangeResponseData
    gateio: ExchangeResponseData
    bybit: ExchangeResponseData

class AsiaExchangeSocket(TypedDict):
    okx: ExchangeResponseData
    gateio: ExchangeResponseData
    bybit: ExchangeResponseData


class AsiaMarketRequestType(TypedDict):
    rest: AsiaExchangeRest
    socket: AsiaExchangeSocket


class WorldMarketsRequestType(TypedDict):
    korea: KoreaMarketRequestType
    asia: AsiaMarketRequestType
    ne: NEMarketRequestType


ForeginMarkets = AsiaMarketRequestType | NEMarketRequestType
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
