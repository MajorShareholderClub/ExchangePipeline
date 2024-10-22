import uuid
from typing import TypedDict, NewType, Generic, TypeVar, Union
from decimal import Decimal


T = TypeVar("T")  # 성공 타입
E = TypeVar("E")  # 오류 타입


class Ok(Generic[T]):
    def __init__(self, value: T) -> None:
        self.value = value


class Err(Generic[E]):
    def __init__(self, error: E) -> None:
        self.error = error


Result = Union[Ok[T], Err[E]]


# request Type
ExchangeResponseData = dict[str, str | int | float | dict[str, int | str]]
ExchangeOrderingData = dict[str, int]
ResponseData = ExchangeResponseData | ExchangeOrderingData

UpbitumbOrderingResponseData = dict[str, int | list[dict[str, int]]]


"""
-----------------------------------------------------
|  Preprocessing Exchanged Present Pirce dataformat |
-----------------------------------------------------
"""
# 전처리 한거래 포맷 데이터
PriceData = dict[str, Decimal | None]


class ExchangeData(TypedDict):
    name: str
    timestamp: float
    coin_symbol: str
    data: PriceData


class KoreaCoinMarketData(TypedDict):
    time: int
    upbit: ExchangeData | bool
    bithumb: ExchangeData | bool
    coinone: ExchangeData | bool
    korbit: ExchangeData | bool


class ForeignCoinMarketData(TypedDict):
    binance: ExchangeData | bool
    kraken: ExchangeData | bool
    okx: ExchangeData | bool
    gateio: ExchangeData | bool


class SocketLowData(TypedDict):
    market: str
    symbol: str
    data: dict | list


class ProducerMetadataDict(TypedDict):
    market: str
    symbol: str
    topic: str
    key: str


ExchangeCollection = dict[str, KoreaCoinMarketData | ForeignCoinMarketData]

"""
-----------------------------
|  websocket parameter Type |
-----------------------------

"""
UUID = NewType("UUID", str(uuid.uuid4()))


class TicketUUID(TypedDict):
    ticket: UUID


# 업빗썸
class CombinedRequest(TypedDict):
    type: str
    codes: list[str]
    isOnlySnapshot: bool
    level: int | None


# 코인원
class CoinoneTopicParameter(TypedDict):
    quote_currency: str
    target_currency: str


# 코인원
class CoinoneSocketParameter(TypedDict):
    request_type: str
    channel: str
    data: CoinoneTopicParameter


# 코빗
class KorbitChannelParameter(TypedDict):
    channels: list[str]


# 코빗
class KorbitSocketParameter(TypedDict):
    accessToken: str | None
    timestamp: int
    event: str
    data: KorbitChannelParameter


# ------------------------------------------------------------------
# --------------------------파라미터 정의-------------------------------
# ------------------------------------------------------------------


class BinanceSocketParameter(TypedDict):
    id: UUID
    method: str
    params: list[str]


class KrakenParameter(TypedDict):
    channel: str
    symbol: list[str]


class KrakenSocketParameter(TypedDict):
    method: str
    params: KrakenParameter


class GateioSocketParameter(TypedDict):
    time: int
    channel: str
    event: str
    payload: list[str]


class OKXArgsSocketParameter(TypedDict):
    channel: str
    instId: str


class OKXSocketParameter(TypedDict):
    op: str
    args: list[OKXArgsSocketParameter]


class BybitSocketParameter(TypedDict):
    req_id: UUID
    op: str
    args: list[str]


UpBithumbSocketParmater = list[TicketUUID | CombinedRequest]
SubScribeFormat = (
    UpBithumbSocketParmater
    | CoinoneSocketParameter
    | KorbitSocketParameter
    | BinanceSocketParameter
    | KrakenSocketParameter
    | GateioSocketParameter
    | OKXSocketParameter
    | BybitSocketParameter
)

# ------------------------------------------------------------------
# -----------------------------거래소 주소 매핑----------------------------
# ------------------------------------------------------------------


# 각 거래소에 대한 타입 정의
class ResponseExchangeURL(TypedDict):
    socket: str
    rest: str


# 각 지역에 대한 URL 구조 정의
class RegionURLs(TypedDict):
    upbit: ResponseExchangeURL
    bithumb: ResponseExchangeURL
    korbit: ResponseExchangeURL
    coinone: ResponseExchangeURL


class AsiaRegionURLs(TypedDict):
    okx: ResponseExchangeURL
    gateio: ResponseExchangeURL
    bybit: ResponseExchangeURL


class NERegionURLs(TypedDict):
    binance: ResponseExchangeURL
    kraken: ResponseExchangeURL


# 전체 URL 구조 정의
class URLs(TypedDict):
    korea: RegionURLs
    asia: AsiaRegionURLs
    ne: NERegionURLs
