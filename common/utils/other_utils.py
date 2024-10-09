from typing import NoReturn
from common.setting.properties import (
    SOCKET_UPBIT_URL,
    SOCKET_BITHUMB_URL,
    SOCKET_COINONE_URL,
)
from common.setting.properties import (
    SOCKET_KRAKEN_URL,
    SOCKET_OKX_URL,
    SOCKET_GATEIO_URL,
    SOCKET_BINANCE_URL,
    SOCKET_BYBIT_URL,
)
from common.setting.properties import (
    REST_UPBIT_URL,
    REST_BITHUMB_URL,
    REST_COINONE_URL,
    REST_KORBIT_URL,
)
from common.setting.properties import (
    REST_BINANCE_URL,
    REST_KRAKEN_URL,
    REST_OKX_URL,
    REST_GATEIO_URL,
    REST_BYBIT_URL,
)


def get_symbol_collect_url(market: str, type_: str) -> str | NoReturn:
    """URL matting

    Args:
        -  market (str): market name \n
        -  type_ (str): U Type \n
    Raises:
        - ValueError: Not Fount market is ValueError string \n
    Returns:
        str: market url
    """
    urls = {
        ("upbit", "socket"): SOCKET_UPBIT_URL,
        ("upbit", "rest"): REST_UPBIT_URL,
        ("bithumb", "socket"): SOCKET_BITHUMB_URL,
        ("bithumb", "rest"): REST_BITHUMB_URL,
        # ("korbit", "socket"): SOCKET_KORBIT_URL,
        ("korbit", "rest"): REST_KORBIT_URL,
        ("coinone", "socket"): SOCKET_COINONE_URL,
        ("coinone", "rest"): REST_COINONE_URL,
        ("binance", "socket"): SOCKET_BINANCE_URL,
        ("binance", "rest"): REST_BINANCE_URL,
        ("kraken", "socket"): SOCKET_KRAKEN_URL,
        ("kraken", "rest"): REST_KRAKEN_URL,
        ("okx", "socket"): SOCKET_OKX_URL,
        ("okx", "rest"): REST_OKX_URL,
        ("gateio", "socket"): SOCKET_GATEIO_URL,
        ("gateio", "rest"): REST_GATEIO_URL,
        ("bybit", "socket"): SOCKET_BYBIT_URL,
        ("bybit", "rest"): REST_BYBIT_URL,
    }

    url = urls.get((market, type_))
    if url is None:
        raise ValueError(f"등록되지 않은 거래소입니다. --> {market}")
    return url
