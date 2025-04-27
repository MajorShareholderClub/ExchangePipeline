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
from common.setting.exchange import SocketParameterFactory
from common.setting.types import ExchangeSocketParameter, ExchangeMetadata
from common.setting.properties import get_symbol_collect_url


# 1. 거래소 이름 → handler class 매핑
EXCHANGE_HANDLERS = {
    "upbit": UpbitWebsocketHandler,
    "bithumb": BithumbWebsocketHandler,
    "korbit": KorbitWebsocketHandler,
    "coinone": CoinoneWebsocketHandler,
    "binance": BinanceWebsocketHandler,
    "kraken": KrakenWebsocketHandler,
    "bybit": BybitWebsocketHandler,
    "okx": OkxWebsocketHandler,
    "gateio": GateioWebsocketHandler,
}


# 2. 단일 함수로 handler/parameter 반환
def get_exchange(
    exchange: str,
    request_type: str,
    symbols: list[str],
) -> ExchangeSocketParameter:
    """
    거래소 이름에 따라 handler class와 소켓 파라미터 생성 결과를 반환
    """
    handler_class: WorldWebSocket | None = EXCHANGE_HANDLERS.get(exchange)
    if handler_class is None:
        raise ValueError(f"지원하지 않는 거래소: {exchange}")

    # 거래소별 기본 설정
    exchange_settings: dict[str, str] = {
        "upbit": "korea",
        "bithumb": "korea",
        "korbit": "korea",
        "coinone": "korea",
        "okx": "asia",
        "gateio": "asia",
        "bybit": "asia",
        "binance": "ne",
        "kraken": "ne",
    }

    # 거래소 설정 가져오기
    region: str | None = exchange_settings.get(exchange)
    url: str | None = get_symbol_collect_url(exchange, region, "socket")

    metadata = ExchangeMetadata(
        region=region,
        url=url,
        exchange_name=exchange,
        request_type=request_type,
    )

    parameter_info: dict | list[dict] = SocketParameterFactory.create_socket_parameter(
        exchange=exchange,
        symbols=symbols,
        req_type=request_type,
    )
    return ExchangeSocketParameter(
        metadata=metadata,
        parameter_info=parameter_info,
        socket_instance=handler_class,
    )
