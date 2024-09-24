import uuid
from common.core.types import (
    UpBithumbSocketParmater,
    TicketUUID,
    CombinedRequest,
    CoinoneSocketParameter,
    CoinoneRequestParameter,
    CoinoneTopicParameter,
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

    return CoinoneRequestParameter(combined_request)
