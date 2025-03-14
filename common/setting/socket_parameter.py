import time
from datetime import datetime, timezone

import uuid
from common.core.types import (
    UpBithumbSocketParmater,
    TicketUUID,
    CombinedRequest,
    CoinoneSocketParameter,
    CoinoneTopicParameter,
    KorbitSocketParameter,
)
from common.core.types import (
    BinanceSocketParameter,
    KrakenSocketParameter,
    KrakenParameter,
    GateioSocketParameter,
    OKXArgsSocketParameter,
    OKXSocketParameter,
    BybitSocketParameter,
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
