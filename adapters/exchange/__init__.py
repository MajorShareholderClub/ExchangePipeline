from .korea import (
    UpbitWebsocketHandler,
    KorbitWebsocketHandler,
    BithumbWebsocketHandler,
    CoinoneWebsocketHandler,
)
from .asia import (
    BybitWebsocketHandler,
    OkxWebsocketHandler,
    GateioWebsocketHandler,
)
from .ne import KrakenWebsocketHandler, BinanceWebsocketHandler


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
    "UpbitWebsocketHandler",
    "KorbitWebsocketHandler",
    "BithumbWebsocketHandler",
    "CoinoneWebsocketHandler",
    "BinanceWebsocketHandler",
    "BybitWebsocketHandler",
    "OkxWebsocketHandler",
    "GateioWebsocketHandler",
    "KrakenWebsocketHandler",
]
