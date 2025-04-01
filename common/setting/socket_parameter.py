import time

import uuid
from common.setting.types import (
    UpBithumbSocketParameter,
    TicketUUID,
    CombinedRequest,
    CoinoneSocketParameter,
    CoinoneTopicParameter,
    KorbitSocketParameter,
)
from common.setting.types import (
    BinanceSocketParameter,
    KrakenSocketParameter,
    KrakenParameter,
    GateioSocketParameter,
    OKXArgsSocketParameter,
    OKXSocketParameter,
    BybitSocketParameter,
)

UUID = str(uuid.uuid4())

# fmt: off
def upbithumb_socket_parameter(symbol: str, req_type: str) -> UpBithumbSocketParameter:
    return [
        TicketUUID(ticket=UUID),
        CombinedRequest(
            type=req_type,
            codes=[f"KRW-{symbol.upper()}"],
            is_only_realtime=True,
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
    return [
        KorbitSocketParameter(
            method="subscribe",
            type=req_type,
            symbols=[f"{symbol.lower()}_krw"]
        )
    ]

def binance_socket_paramater(symbol: str, req_type: str) -> BinanceSocketParameter:
    return BinanceSocketParameter(
        id=UUID,
        method=f"SUBSCRIBE",
        params=[f"{symbol.lower()}usdt@{req_type}"],
    )

def kraken_socket_parameter(symbol: str, req_type: str) -> KrakenSocketParameter:
    return KrakenSocketParameter(
        method="subscribe",
        params=KrakenParameter(
            channel=f"{req_type}", 
            symbol=[f"{symbol.upper()}/USD"],
            event_trigger="trades",
            snapshot=False
        ),
        req_id=UUID
    )

def gateio_socket_parameter(symbol: str, req_type: str) -> GateioSocketParameter:
    return GateioSocketParameter(
        time=int(time.time()),
        channel=f"spot.{req_type}",
        event="subscribe",
        payload=[f"{symbol.upper()}_USDT"]
    )

def bybit_socket_parameter(symbol: str, req_type: str) -> BybitSocketParameter:
    return BybitSocketParameter(
        req_id=UUID,
        op="subscribe",
        args=[f"{req_type}.{symbol.upper()}USDT"]
    )

def okx_socket_parameter(symbol: str, req_type: str) -> OKXSocketParameter:
    return OKXSocketParameter(
        op="subscribe",
        args=[OKXArgsSocketParameter(channel=req_type, instId=f"{symbol}-USDT")],
    )
