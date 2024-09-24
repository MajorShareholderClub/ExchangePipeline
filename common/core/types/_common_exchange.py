import uuid
from typing import TypedDict, NewType
from decimal import Decimal


# request Type
ExchangeResponseData = dict[str, str | int | float]
ExchangeOrderingData = dict[str, int]
UpbitumbOrderingResponseData = dict[str, int | list[dict[str, int]]]


"""
-----------------------------------------------------
|  Preprocessing Exchanged Present Pirce dataformat |
-----------------------------------------------------
"""
# fmt: off
# 전처리 한거래 포맷 데이터
PriceData = dict[str, Decimal | None]
class ExchangeData(TypedDict):
    name: str
    coin_symbol: str
    data: PriceData


class KoreaCoinMarketData(TypedDict):
    time: int
    upbit: ExchangeData | bool
    bithumb: ExchangeData | bool
    coinone: ExchangeData | bool
    korbit: ExchangeData | bool


class ForeignCoinMarketData(TypedDict):
    time: int
    binance: ExchangeData | bool
    kraken: ExchangeData | bool
    okx: ExchangeData | bool
    gateio: ExchangeData | bool
    htx: ExchangeData | bool
    # coinbase: ExchangeData | bool


"""
-----------------------------------
|  korea websocket parameter Type |
-----------------------------------

"""
# 업빗썸
# fmt: off
UUID = NewType("UUID", str(uuid.uuid4()))
class TicketUUID(TypedDict):
    ticket: UUID


# 업빗썸
class CombinedRequest(TypedDict):
    type: str
    codes: list[str]
    level: int | None


# 코인원
class CoinoneTopicParameter(TypedDict):
    quote_currency: str
    target_currency: str


# 코인원
class CoinoneRequestParameter(TypedDict):
    request_type: str
    channel: str
    topic: CoinoneTopicParameter


CoinoneSocketParameter = CoinoneRequestParameter
UpBithumbSocketParmater = list[TicketUUID | CombinedRequest]
SubScribeFormat = UpBithumbSocketParmater | CoinoneSocketParameter
