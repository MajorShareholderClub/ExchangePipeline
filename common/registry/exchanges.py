from adapters.exchange import WorldWebSocket
from adapters.exchange.korea import (
    UpbitWebsocketHandler,
    KorbitWebsocketHandler,
    BithumbWebsocketHandler,
    CoinoneWebsocketHandler,
)
from adapters.exchange import (
    BybitWebsocketHandler,
    OkxWebsocketHandler,
    GateioWebsocketHandler,
)
from adapters.exchange.ne import KrakenWebsocketHandler, BinanceWebsocketHandler
from common.setting.parameter.connection_parameter import get_exchange_config


def get_all_exchanges(request_type: str) -> dict[str, dict[str, WorldWebSocket]]:
    """모든 거래소 정보를 반환하는 함수"""
    return {
        "upbit": {
            "parameter_info": get_exchange_config("upbit", request_type).build(),
            "socket": UpbitWebsocketHandler,
        },
        "bithumb": {
            "parameter_info": get_exchange_config("bithumb", request_type).build(),
            "socket": BithumbWebsocketHandler,
        },
        "korbit": {
            "parameter_info": get_exchange_config("korbit", request_type).build(),
            "socket": KorbitWebsocketHandler,
        },
        "coinone": {
            "parameter_info": get_exchange_config("coinone", request_type).build(),
            "socket": CoinoneWebsocketHandler,
        },
        "binance": {
            "parameter_info": get_exchange_config("binance", request_type).build(),
            "socket": BinanceWebsocketHandler,
        },
        "bybit": {
            "parameter_info": get_exchange_config("bybit", request_type).build(),
            "socket": BybitWebsocketHandler,
        },
        "okx": {
            "parameter_info": get_exchange_config("okx", request_type).build(),
            "socket": OkxWebsocketHandler,
        },
        "gateio": {
            "parameter_info": get_exchange_config("gateio", request_type).build(),
            "socket": GateioWebsocketHandler,
        },
        "kraken": {
            "parameter_info": get_exchange_config("kraken", request_type).build(),
            "socket": KrakenWebsocketHandler,
        },
    }


def get_exchange(
    exchange_name: str, request_type: str
) -> dict[str, WorldWebSocket] | None:
    """특정 거래소의 연결 정보를 반환하는 함수"""
    return get_all_exchanges(request_type).get(exchange_name)
