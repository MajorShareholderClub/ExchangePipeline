import uuid
from common.core.types import (
    UpBithumbSocketParmater,
    TicketUUID,
    TickerWebSocketRequest,
    CoinoneSocketParameter,
    CoinoneRequestParameter,
    CoinoneTopicParameter,
)


def upbithumb_socket_parameter(symbol: str) -> UpBithumbSocketParmater:
    return [
        TicketUUID(ticket=str(uuid.uuid4())),
        TickerWebSocketRequest(
            type="ticker",
            codes=[f"KRW-{symbol.upper()}"],
            isOnlyRealtime=True,
        ),
    ]


def coinone_socket_parameter(symbol: str) -> CoinoneSocketParameter:
    return CoinoneRequestParameter(
        request_type="SUBSCRIBE",
        channel="TICKER",
        topic=CoinoneTopicParameter(
            quote_currency="KRW", target_currency=f"{symbol.upper()}"
        ),
    )
