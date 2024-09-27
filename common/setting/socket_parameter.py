import time
import uuid
from common.core.types import (
    UpBithumbSocketParmater,
    TicketUUID,
    CombinedRequest,
    CoinoneSocketParameter,
    CoinoneTopicParameter,
    BinanceSocketParameter,
    KrakenSocketParameter,
    KrakenSubScription,
    GateioSocketParameter,
    OKXArgsSocketParameter,
    OKXSocketParameter,
)


def upbithumb_socket_parameter(
    symbol: str, req_type: str | None = None
) -> UpBithumbSocketParmater:
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
        TicketUUID(ticket=str(uuid.uuid4())),
        CombinedRequest(combined_request),
    ]


def coinone_socket_parameter(
    symbol: str, req_type: str | None = None
) -> CoinoneSocketParameter:
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


def binance_socket_paramater(
    symbol: str, req_type: str | None = None
) -> BinanceSocketParameter:

    return BinanceSocketParameter(
        id=str(uuid.uuid4()),
        method=f"SUBSCRIBE",
        params=[f"{symbol.lower()}usdt@{req_type}"],
    )


def kraken_socket_parameter(
    symbol: str, req_type: str | None = None
) -> KrakenSocketParameter:
    return KrakenSocketParameter(
        event="subscribe",
        pair=[f"{symbol}/USD"],
        subscription=KrakenSubScription(name=f"{req_type}"),
    )


def gateio_socket_parameter(
    symbol: str, req_type: str | None = None
) -> GateioSocketParameter:
    return GateioSocketParameter(
        time=int(time.time()),
        channel=f"spot.{req_type}",
        event="subscribe",
        payload=[f"{symbol.upper()}_USDT"],
    )


def okx_socket_parameter(
    symbol: str, req_type: str | None = None
) -> OKXSocketParameter:
    return OKXSocketParameter(
        op="subscribe",
        args=[OKXArgsSocketParameter(channel=req_type, instId=f"{symbol}-USDT")],
    )


def bybit_socket_parameter(symbol: str, req_type: str | None = None):
    return {
        "req_id": str(uuid.uuid4()),
        "op": "subscribe",
        "args": [f"{req_type}.{symbol.upper()}USDT"],
    }
