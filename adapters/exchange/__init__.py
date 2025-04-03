from .korea import (
    UpbitWebsocketHandler,
    KorbitWebsocketHandler,
    BithumbWebsocketHandler,
    CoinoneWebsocketHandler,
)
from .asia import (
    BinanceWebsocketHandler,
    BybitWebsocketHandler,
    OkxWebsocketHandler,
    GateioWebsocketHandler,
)
from .ne import KrakenWebsocketHandler


WorldWebSocket = (
    UpbitWebsocketHandler
    | KorbitWebsocketHandler
    | BithumbWebsocketHandler
    | CoinoneWebsocketHandler
    | BinanceWebsocketHandler
    | BybitWebsocketHandler
    | OkxWebsocketHandler
    | GateioWebsocketHandler
    | KrakenWebsocketHandler
)

__all__ = [
    "WorldWebSocket",
]
