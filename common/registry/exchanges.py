from adapters.exchange import WorldWebSocket
from adapters.exchange.korea import (
    UpbitWebsocketHandler,
    KorbitWebsocketHandler,
    BithumbWebsocketHandler,
    CoinoneWebsocketHandler,
)
from adapters.exchange.asia import (
    BinanceWebsocketHandler,
    BybitWebsocketHandler,
    OkxWebsocketHandler,
    GateioWebsocketHandler,
)
from adapters.exchange.ne import KrakenWebsocketHandler
from common.setting.parameter.connection_parameter import (
    upbit_config,
    korbit_config,
    bithumb_config,
    coinone_config,
    binance_config,
    bybit_config,
    okx_config,
    gateio_config,
    kraken_config,
)


def get_all_exchanges() -> dict[str, dict[str, WorldWebSocket]]:
    """모든 거래소 정보를 반환하는 함수"""
    return {
        "upbit": {
            "url": upbit_config.build(),
            "socket": UpbitWebsocketHandler,
        },
        "korbit": {
            "url": korbit_config.build(),
            "socket": KorbitWebsocketHandler,
        },
        "bithumb": {
            "url": bithumb_config.build(),
            "socket": BithumbWebsocketHandler,
        },
        "coinone": {
            "url": coinone_config.build(),
            "socket": CoinoneWebsocketHandler,
        },
        "binance": {
            "url": binance_config.build(),
            "socket": BinanceWebsocketHandler,
        },
        "bybit": {
            "url": bybit_config.build(),
            "socket": BybitWebsocketHandler,
        },
        "okx": {
            "url": okx_config.build(),
            "socket": OkxWebsocketHandler,
        },
        "gateio": {
            "url": gateio_config.build(),
            "socket": GateioWebsocketHandler,
        },
        "kraken": {
            "url": kraken_config.build(),
            "socket": KrakenWebsocketHandler,
        },
    }


def get_exchange(exchange_name: str) -> WorldWebSocket | None:
    """특정 거래소의 연결 정보를 반환하는 함수"""
    return get_all_exchanges().get(exchange_name)
