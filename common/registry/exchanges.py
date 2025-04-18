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
from common.setting.parameter.connection_parameter import get_exchange_config


def get_all_exchanges() -> dict[str, dict[str, WorldWebSocket]]:
    """모든 거래소 정보를 반환하는 함수"""
    return {
        "upbit": {
            "parameter_info": get_exchange_config("upbit", "ticker").build(),
            "socket": UpbitWebsocketHandler,
        },
        # "bithumb": {
        #     "parameter_info": bithumb_config_ticker.build(),
        #     "socket": BithumbWebsocketHandler,
        # },
        # "korbit": {
        #     "parameter_info": korbit_config_ticker.build(),
        #     "socket": KorbitWebsocketHandler,
        # },
        # "coinone": {
        #     "parameter_info": coinone_config_ticker.build(),
        #     "socket": CoinoneWebsocketHandler,
        # },
        # "binance": {
        #     "parameter_info": binance_config_ticker.build(),
        #     "socket": BinanceWebsocketHandler,
        # },
        # "bybit": {
        #     "parameter_info": bybit_config_ticker.build(),
        #     "socket": BybitWebsocketHandler,
        # },
        # "okx": {
        #     "parameter_info": okx_config_ticker.build(),
        #     "socket": OkxWebsocketHandler,
        # },
        # "gateio": {
        #     "parameter_info": gateio_config_ticker.build(),
        #     "socket": GateioWebsocketHandler,
        # },
        # "kraken": {
        #     "parameter_info": kraken_config_ticker.build(),
        #     "socket": KrakenWebsocketHandler,
        # },
    }


def get_exchange(exchange_name: str) -> dict[str, WorldWebSocket] | None:
    """특정 거래소의 연결 정보를 반환하는 함수"""
    return get_all_exchanges().get(exchange_name)
