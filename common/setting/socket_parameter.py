import time
from datetime import datetime, timezone

import uuid
from common.core.types import (
    UpBithumbSocketParmater,
    TicketUUID,
    CombinedRequest,
    CoinoneSocketParameter,
    CoinoneTopicParameter,
    KorbitChannelParameter,
    KorbitSocketParameter,
)
from common.core.types import (
    BinanceSocketParameter,
    KrakenSocketParameter,
    KrakenSubScription,
    GateioSocketParameter,
    OKXArgsSocketParameter,
    OKXSocketParameter,
    BybitSocketParameter,
)

uu_id = str(uuid.uuid4())


# fmt: off
def upbithumb_socket_parameter(symbol: str, req_type: str) -> UpBithumbSocketParmater:
    combined_request = {
        "type": req_type,
        "codes": [f"KRW-{symbol.upper()}"],
    }

    # req_type에 따라 isOnlyRealtime 추가
    if req_type == "ticker":  # 필요한 타입에 맞게 수정
        combined_request["isOnlyRealtime"] = True
    elif req_type == "orderbook":
        combined_request["level"] = 1000

    return [
        TicketUUID(ticket=uu_id),
        CombinedRequest(combined_request),
    ]


def coinone_socket_parameter(symbol: str, req_type: str) -> CoinoneSocketParameter:
    combined_request = {
        "request_type": "SUBSCRIBE",
        "topic": CoinoneTopicParameter(
            quote_currency="KRW", target_currency=f"{symbol.upper()}"
        ),
    }

    if req_type.upper() == "TICKER":
        combined_request["channel"] = "TICKER"
    elif req_type.upper() == "ORDERBOOK":
        combined_request["channel"] = "ORDERBOOK"

    return CoinoneSocketParameter(combined_request)


def korbit_socket_parameter(symbol: str, req_type: str) -> KorbitSocketParameter:
    return KorbitSocketParameter(
        accessToken=None,
        timestamp=int(datetime.now(timezone.utc).timestamp()),
        event="korbit:subscribe",
        data=KorbitChannelParameter(
            channels=[f"{req_type}:{symbol.lower()}_krw"]
        )
    )


def binance_socket_paramater(symbol: str, req_type: str) -> BinanceSocketParameter:
    return BinanceSocketParameter(
        id=uu_id,
        method=f"SUBSCRIBE",
        params=[f"{symbol.lower()}usdt@{req_type}"],
    )


def kraken_socket_parameter(symbol: str, req_type: str) -> KrakenSocketParameter:
    return KrakenSocketParameter(
        event="subscribe",
        pair=[f"{symbol}/USD"],
        subscription=KrakenSubScription(name=f"{req_type}"),
    )


def gateio_socket_parameter(symbol: str, req_type: str) -> GateioSocketParameter:
    return GateioSocketParameter(
        time=int(time.time()),
        channel=f"spot.{req_type}",
        event="subscribe",
        payload=[f"{symbol.upper()}_USDT"],
    )


def bybit_socket_parameter(symbol: str, req_type: str) -> BybitSocketParameter:
    return BybitSocketParameter(
        req_id=uu_id,
        op="subscribe",
        args=[f"{req_type}.{symbol.upper()}USDT"],
    )


def okx_socket_parameter(symbol: str, req_type: str) -> OKXSocketParameter:
    return OKXSocketParameter(
        op="subscribe",
        args=[OKXArgsSocketParameter(channel=req_type, instId=f"{symbol}-USDT")],
    )
