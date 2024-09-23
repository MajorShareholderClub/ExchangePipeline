import configparser
from pathlib import Path

path = Path(__file__).parent
parser = configparser.ConfigParser()
parser.read(f"{path}/urls.conf")

BTC_TOPIC_NAME = parser.get("TOPICNAME", "BTC_TOPIC_NAME")
ETH_TOPIC_NAME = parser.get("TOPICNAME", "ETHER_TOPIC_NAME")
# OTHER_TOPIC_NAME = parser.get("TOPICNAME", "OTHER_TOPIC_NAME")

REST_BTC_AVERAGE_TOPIC_NAME = parser.get(
    "AVERAGETOPICNAME", "BTC_REST_AVERAGE_TOPIC_NAME"
)
REST_ETH_AVERAGE_TOPIC_NAME = parser.get(
    "AVERAGETOPICNAME", "ETHER_REST_AVERAGE_TOPIC_NAME"
)
SOCKET_BTC_AVERAGE_TOPIC_NAME = parser.get(
    "AVERAGETOPICNAME", "BTC_SOCKET_AVERAGE_TOPIC_NAME"
)
SOCKET_ETH_AVERAGE_TOPIC_NAME = parser.get(
    "AVERAGETOPICNAME", "ETHER_SOCKET_AVERAGE_TOPIC_NAME"
)


BTC_TOPIC_NAME = parser.get("TOPICNAME", "BTC_TOPIC_NAME")
ETH_TOPIC_NAME = parser.get("TOPICNAME", "ETHER_TOPIC_NAME")

REST_UPBIT_URL = parser.get("APIURL", "UPBIT")
REST_BITHUMB_URL = parser.get("APIURL", "BITHUMB")
REST_KORBIT_URL = parser.get("APIURL", "KORBIT")
REST_COINONE_URL = parser.get("APIURL", "COINONE")

SOCKET_UPBIT_URL = parser.get("SOCKETURL", "UPBIT")
SOCKET_BITHUMB_URL = parser.get("SOCKETURL", "BITHUMB")
SOCKET_KORBIT_URL = parser.get("SOCKETURL", "KORBIT")
SOCKET_COINONE_URL = parser.get("SOCKETURL", "COINONE")


MAXLISTSIZE = 10

UPBIT_BTC_REAL_TOPIC_NAME = parser.get("REALTIMETOPICNAME", "UPBIT_BTC_REAL_TOPIC_NAME")
BITHUMB_BTC_REAL_TOPIC_NAME = parser.get(
    "REALTIMETOPICNAME", "BITHUMB_BTC_REAL_TOPIC_NAME"
)
KORBIT_BTC_REAL_TOPIC_NAME = parser.get(
    "REALTIMETOPICNAME", "KORBIT_BTC_REAL_TOPIC_NAME"
)
COINONE_BTC_REAL_TOPIC_NAME = parser.get(
    "REALTIMETOPICNAME", "COINONE_BTC_REAL_TOPIC_NAME"
)


# KAFKA
BOOTSTRAP_SERVER = parser.get("KAFKA", "bootstrap_servers")
SECURITY_PROTOCOL = parser.get("KAFKA", "security_protocol")
MAX_BATCH_SIZE = parser.get("KAFKA", "max_batch_size")
MAX_REQUEST_SIZE = parser.get("KAFKA", "max_request_size")
ARCKS = parser.get("KAFKA", "acks")
{
    "symbol": "BTC/USDT",
    "timestamp": 1727061107024,
    "datetime": "2024-09-23T03:11:47.024Z",
    "high": 64431.82,
    "low": 62357.93,
    "bid": 64386.0,
    "bidVolume": 0.37675,
    "ask": 64386.01,
    "askVolume": 4.88628,
    "vwap": 63164.35196406,
    "open": 63127.99,
    "close": 64386.01,
    "last": 64386.01,
    "previousClose": 63128.0,
    "change": 1258.02,
    "percentage": 1.993,
    "average": 63757.0,
    "baseVolume": 17587.26254,
    "quoteVolume": 1110888041.160866,
    "info": {
        "symbol": "BTCUSDT",
        "priceChange": "1258.02000000",
        "priceChangePercent": "1.993",
        "weightedAvgPrice": "63164.35196406",
        "prevClosePrice": "63128.00000000",
        "lastPrice": "64386.01000000",
        "lastQty": "0.00040000",
        "bidPrice": "64386.00000000",
        "bidQty": "0.37675000",
        "askPrice": "64386.01000000",
        "askQty": "4.88628000",
        "openPrice": "63127.99000000",
        "highPrice": "64431.82000000",
        "lowPrice": "62357.93000000",
        "volume": "17587.26254000",
        "quoteVolume": "1110888041.16086600",
        "openTime": "1726974707024",
        "closeTime": "1727061107024",
        "firstId": "3843949973",
        "lastId": "3846704240",
        "count": "2754268",
    },
}
