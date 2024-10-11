import configparser
from pathlib import Path
from typing import NoReturn

path = Path(__file__).parent
parser = configparser.ConfigParser()
parser.read(f"{path}/urls.conf")

BTC_TOPIC_NAME = parser.get("TOPICNAME", "BTC_TOPIC_NAME")
ETH_TOPIC_NAME = parser.get("TOPICNAME", "ETHER_TOPIC_NAME")


BTC_TOPIC_NAME = parser.get("TOPICNAME", "BTC_TOPIC_NAME")
ETH_TOPIC_NAME = parser.get("TOPICNAME", "ETHER_TOPIC_NAME")

# 국내 거래소
REST_UPBIT_URL = parser.get("APIURL", "UPBIT")
REST_BITHUMB_URL = parser.get("APIURL", "BITHUMB")
REST_KORBIT_URL = parser.get("APIURL", "KORBIT")
REST_COINONE_URL = parser.get("APIURL", "COINONE")

# 해외 거래소
REST_BINANCE_URL = parser.get("APIURL", "BINANCE")
REST_KRAKEN_URL = parser.get("APIURL", "KRAKEN")
REST_OKX_URL = parser.get("APIURL", "OKX")
REST_GATEIO_URL = parser.get("APIURL", "GATEIO")
REST_BYBIT_URL = parser.get("APIURL", "BYBIT")
REST_COINBASE_URL = parser.get("APIURL", "COINBASE")


# 국내 거래소
SOCKET_UPBIT_URL = parser.get("SOCKETURL", "UPBIT")
SOCKET_BITHUMB_URL = parser.get("SOCKETURL", "BITHUMB")
SOCKET_KORBIT_URL = parser.get("SOCKETURL", "KORBIT")
SOCKET_COINONE_URL = parser.get("SOCKETURL", "COINONE")

# 해외 거래소
SOCKET_BINANCE_URL = parser.get("SOCKETURL", "BINANCE")
SOCKET_KRAKEN_URL = parser.get("SOCKETURL", "KRAKEN")
SOCKET_OKX_URL = parser.get("SOCKETURL", "OKX")
SOCKET_GATEIO_URL = parser.get("SOCKETURL", "GATEIO")
SOCKET_BYBIT_URL = parser.get("SOCKETURL", "BYBIT")
SOCKET_COINBASE_URL = parser.get("SOCKETURL", "COINBASE")


MAXLISTSIZE = 10

UPBIT_BTC_REAL_TOPIC_NAME = parser.get(
    "KOREAREALTIMETOPICNAME", "UPBIT_BTC_REAL_TOPIC_NAME"
)
BITHUMB_BTC_REAL_TOPIC_NAME = parser.get(
    "KOREAREALTIMETOPICNAME", "BITHUMB_BTC_REAL_TOPIC_NAME"
)
KORBIT_BTC_REAL_TOPIC_NAME = parser.get(
    "KOREAREALTIMETOPICNAME", "KORBIT_BTC_REAL_TOPIC_NAME"
)
COINONE_BTC_REAL_TOPIC_NAME = parser.get(
    "KOREAREALTIMETOPICNAME", "COINONE_BTC_REAL_TOPIC_NAME"
)


# KAFKA
BOOTSTRAP_SERVER = parser.get("KAFKA", "bootstrap_servers")
SECURITY_PROTOCOL = parser.get("KAFKA", "security_protocol")
MAX_BATCH_SIZE = parser.get("KAFKA", "max_batch_size")
MAX_REQUEST_SIZE = parser.get("KAFKA", "max_request_size")
ARCKS = parser.get("KAFKA", "acks")


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
        ("korbit", "socket"): SOCKET_KORBIT_URL,
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
        ("coinbase", "socket"): SOCKET_COINBASE_URL,
        ("coinbase", "rest"): REST_COINBASE_URL,
    }

    url = urls.get((market, type_))
    if url is None:
        raise ValueError(f"등록되지 않은 거래소입니다. --> {market}")
    return url
