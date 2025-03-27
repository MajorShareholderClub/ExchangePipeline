from typing import TypedDict, NewType
from decimal import Decimal
from datetime import datetime

import time
import uuid


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


uu_id = str(uuid.uuid4())


# fmt: off
def upbithumb_socket_parameter(symbol: str, req_type: str) -> UpBithumbSocketParmater:
    return [
        TicketUUID(ticket=uu_id),
        CombinedRequest(
            type=req_type,
            codes=[f"KRW-{symbol.upper()}"],
            isOnlyRealtime=True,
        )
    ]


def coinone_socket_parameter(symbol: str, req_type: str) -> CoinoneSocketParameter:
    return CoinoneSocketParameter(
        request_type="SUBSCRIBE",
        channel=req_type.upper(),
        topic=CoinoneTopicParameter(
            quote_currency="KRW", target_currency=f"{symbol.upper()}"
        ),
    )


def korbit_socket_parameter(symbol: str, req_type: str) -> list[KorbitSocketParameter]:
    return [KorbitSocketParameter(
        method="subscribe",
        type=req_type,
        symbols=[f"{symbol.lower()}_krw"]
    )]



def binance_socket_paramater(symbol: str, req_type: str) -> BinanceSocketParameter:
    return BinanceSocketParameter(
        id=uu_id,
        method=f"SUBSCRIBE",
        params=[f"{symbol.lower()}usdt@{req_type}"],
    )


def kraken_socket_parameter(symbol: str, req_type: str) -> KrakenSocketParameter:
    kraken = KrakenSocketParameter(
        method="subscribe",
        params=KrakenParameter(
            channel=f"{req_type}", 
            symbol=[f"{symbol.upper()}/USD"],
            event_trigger="trades",
            snapshot=False
        ),
        req_id=1234
    )
    
    if req_type == "book":
        kraken["req_id"] = int(datetime.now().timestamp())
    
    return kraken


def gateio_socket_parameter(symbol: str, req_type: str) -> GateioSocketParameter:
    gate_io = GateioSocketParameter(
        time=int(time.time()),
        channel=f"spot.{req_type}",
        event="subscribe",
    )
    
    if req_type == "order_book":
        gate_io["payload"] = [f"{symbol.upper()}_USDT", "100", "100ms"]
    elif req_type == "tickers":
        gate_io["payload"] =[f"{symbol.upper()}_USDT"]
        
    return gate_io

def bybit_socket_parameter(symbol: str, req_type: str) -> BybitSocketParameter:
    bybit = BybitSocketParameter(
        req_id=uu_id,
        op="subscribe",
    )
    if req_type == "orderbook":
        bybit["args"] = [f"{req_type}.50.{symbol.upper()}USDT"]

    elif req_type == "tickers":
        bybit["args"] = [f"{req_type}.{symbol.upper()}USDT"]
    
    return bybit

def okx_socket_parameter(symbol: str, req_type: str) -> OKXSocketParameter:
    return OKXSocketParameter(
        op="subscribe",
        args=[OKXArgsSocketParameter(channel=req_type, instId=f"{symbol}-USDT")],
    )
