from dataclasses import dataclass
from typing import TypedDict, NewType, TypeVar, Generic, Union
from decimal import Decimal

T = TypeVar("T")  # 성공 타입
E = TypeVar("E")  # 오류 타입


class Ok(Generic[T]):
    def __init__(self, value: T) -> None:
        self.value = value


class Err(Generic[E]):
    def __init__(self, error: E) -> None:
        self.error = error


# request Type
ExchangeResponseData = dict[str, str | int | float | dict[str, int | str]]
ExchangeOrderingData = dict[str, int]
ResponseData = ExchangeResponseData | ExchangeOrderingData
UpbitumbOrderingResponseData = dict[str, int | list[dict[str, int]]]
Result = Union[Ok[T], Err[E]]


"""
-----------------------------------------------------
|  Preprocessing Exchanged Present Pirce dataformat |
-----------------------------------------------------
"""
# 전처리 한거래 포맷 데이터
PriceData = dict[str, Decimal | None]


@dataclass(frozen=True)
class CoinDataInfo:
    market: str
    timestamp: int | float
    symbol: str
    data: tuple[str]


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
    region: str
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
UUID = NewType("UUID", str)


class TicketUUID(TypedDict):
    ticket: UUID


# 업빗썸
class CombinedRequest(TypedDict):
    type: str
    codes: list[str]
    is_only_realtime: bool


# 코인원
class CoinoneTopicParameter(TypedDict):
    quote_currency: str
    target_currency: str


# 코인원
class CoinoneSocketParameter(TypedDict):
    request_type: str
    channel: str
    topic: CoinoneTopicParameter


# 코빗
class KorbitSocketParameter(TypedDict):
    method: str
    type: str
    symbols: list[str]


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
    event_trigger: str
    snapshot: bool
    req_id: UUID


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


UpBithumbSocketParameter = list[TicketUUID | CombinedRequest]


# ------------------------------------------------------------------
# -----------------------------거래소 주소 매핑----------------------------
# ------------------------------------------------------------------


# 각 지역에 대한 URL 구조 정의
class KoreaRegionURLs(TypedDict):
    upbit: str
    bithumb: str
    korbit: str
    coinone: str


class AsiaRegionURLs(TypedDict):
    okx: str
    gateio: str
    bybit: str


class NERegionURLs(TypedDict):
    binance: str
    kraken: str


# 전체 URL 구조 정의
class URLs(TypedDict):
    korea: KoreaRegionURLs
    asia: AsiaRegionURLs
    ne: NERegionURLs
