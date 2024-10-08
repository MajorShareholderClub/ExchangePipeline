import configparser
from pathlib import Path

path = Path(__file__).parent
parser = configparser.ConfigParser()
parser.read(f"{path}/urls.conf")

BTC_TOPIC_NAME = parser.get("TOPICNAME", "BTC_TOPIC_NAME")
ETH_TOPIC_NAME = parser.get("TOPICNAME", "ETHER_TOPIC_NAME")
# OTHER_TOPIC_NAME = parser.get("TOPICNAME", "OTHER_TOPIC_NAME")

# REST_BTC_AVERAGE_TOPIC_NAME = parser.get(
#     "AVERAGETOPICNAME", "BTC_REST_AVERAGE_TOPIC_NAME"
# )
# REST_ETH_AVERAGE_TOPIC_NAME = parser.get(
#     "AVERAGETOPICNAME", "ETHER_REST_AVERAGE_TOPIC_NAME"
# )
# SOCKET_BTC_AVERAGE_TOPIC_NAME = parser.get(
#     "AVERAGETOPICNAME", "BTC_SOCKET_AVERAGE_TOPIC_NAME"
# )
# SOCKET_ETH_AVERAGE_TOPIC_NAME = parser.get(
#     "AVERAGETOPICNAME", "ETHER_SOCKET_AVERAGE_TOPIC_NAME"
# )


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
