import uuid
from typing import TypedDict, NewType
from decimal import Decimal


ExchangeResponseData = dict[str, str | int | float]

TIMESTAMP = NewType("TIMESTAMP", int)


class SocketJsonType(TypedDict):
    timestamp: TIMESTAMP
    parameter: list[str]


class RestJsonType(TypedDict):
    parameter: list[str]


class MarketRequestJsonType(TypedDict):
    market: SocketJsonType | RestJsonType


KoreaMarketsLoadJson = MarketRequestJsonType

PriceData = dict[str, Decimal]


class ExchangeData(TypedDict):
    name: str
    coin_symbol: str
    data: dict[str, Decimal]


class KoreaCoinMarketData(TypedDict):
    """
    모든 마켓 타입 스키마 제작
    -  동일한 컬럼 값의 대한 타입 시스템
    """

    time: int
    upbit: ExchangeData | bool
    bithumb: ExchangeData | bool
    coinone: ExchangeData | bool
    korbit: ExchangeData | bool


class ForeignCoinMarketData(TypedDict):
    """
    모든 마켓 타입 스키마 제작
    -  동일한 컬럼 값의 대한 타입 시스템
    """

    time: int
    binance: ExchangeData | bool
    kraken: ExchangeData | bool
    okx: ExchangeData | bool
    gateio: ExchangeData | bool
    htx: ExchangeData | bool
    coinbase: ExchangeData | bool


UUID = NewType("UUID", str(uuid.uuid4()))


class TicketUUID(TypedDict):
    ticket: UUID


class TickerWebSocketRequest(TypedDict):
    type: str
    codes: list[str]
    stream_type: bool


UpBithumbSocketParmater = list[TicketUUID, TickerWebSocketRequest]


class CoinoneTopicParameter(TypedDict):
    quote_currency: str
    target_currency: str


class CoinoneRequestParameter(TypedDict):
    request_type: str
    channel: str
    topic: CoinoneTopicParameter


CoinoneSocketParameter = CoinoneRequestParameter

SubScribeFormat = UpBithumbSocketParmater | CoinoneSocketParameter
