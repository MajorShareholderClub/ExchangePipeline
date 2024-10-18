import configparser
from pathlib import Path
from common.core.types import (
    URLs,
    RegionURLs,
    AsiaRegionURLs,
    NERegionURLs,
    ResponseExchangeURL,
    Result,
    Ok,
    Err,
)

# ConfigParser 설정
path = Path(__file__).parent
parser = configparser.ConfigParser()
parser.read(f"{path}/urls.conf")


# topic
KOREA_REAL_TOPIC_NAME = parser.get("REALTIMETOPICNAME", "KOREA_REAL_TOPIC_NAME")
ASIA_REAL_TOPIC_NAME = parser.get("REALTIMETOPICNAME", "ASIA_REAL_TOPIC_NAME")
NE_REAL_TOPIC_NAME = parser.get("REALTIMETOPICNAME", "NE_REAL_TOPIC_NAME")


# KAFKA
BOOTSTRAP_SERVER = parser.get("KAFKA", "bootstrap_servers")
SECURITY_PROTOCOL = parser.get("KAFKA", "security_protocol")
MAX_BATCH_SIZE = parser.get("KAFKA", "max_batch_size")
MAX_REQUEST_SIZE = parser.get("KAFKA", "max_request_size")
ARCKS = parser.get("KAFKA", "acks")


# URL 가져오는 함수
# fmt: off
def get_exchange_urls() -> URLs:
    return URLs(
        korea=RegionURLs(
            upbit=ResponseExchangeURL(socket=parser.get("SOCKETURL", "UPBIT"), rest=parser.get("RESTURL", "UPBIT")),
            bithumb=ResponseExchangeURL(socket=parser.get("SOCKETURL", "BITHUMB"), rest=parser.get("RESTURL", "BITHUMB")),
            korbit=ResponseExchangeURL(socket=parser.get("SOCKETURL", "KORBIT"), rest=parser.get("RESTURL", "KORBIT")),
            coinone=ResponseExchangeURL(socket=parser.get("SOCKETURL", "COINONE"), rest=parser.get("RESTURL", "COINONE")),
        ),
        asia=AsiaRegionURLs(
            okx=ResponseExchangeURL(socket=parser.get("SOCKETURL", "OKX"),  rest=parser.get("RESTURL", "OKX")),
            gateio=ResponseExchangeURL(socket=parser.get("SOCKETURL", "GATEIO"), rest=parser.get("RESTURL", "GATEIO")),
            bybit=ResponseExchangeURL(socket=parser.get("SOCKETURL", "BYBIT"), rest=parser.get("RESTURL", "BYBIT")),
        ),
        ne=NERegionURLs(
            binance=ResponseExchangeURL(socket=parser.get("SOCKETURL", "BINANCE"), rest=parser.get("RESTURL", "BINANCE")),
            kraken=ResponseExchangeURL(socket=parser.get("SOCKETURL", "KRAKEN"), rest=parser.get("RESTURL", "KRAKEN")),
            coinbase=ResponseExchangeURL(socket=parser.get("SOCKETURL", "COINBASE"), rest=parser.get("RESTURL", "COINBASE")),
        ),
    )


def get_symbol_collect_url(market: str, type_: str, location: str) -> Result[str, str]:
    """URL 매칭

    Args:
        market (str): 거래소 이름
        type_ (str): URL 타입 (socket 또는 rest)
        location (str): 지역 정보

    Raises:
        ValueError: 등록되지 않은 지역 또는 거래소

    Returns:
        str: 매칭된 URL
    """
    # location에 해당하는 딕셔너리 가져오기
    urls: URLs = get_exchange_urls()
    region_urls = urls.get(location)
    ex_urls = region_urls.get(market)
    response_url = ex_urls.get(type_)
    
    match urls.get(location):
        case None:
            return Err(f"등록되지 않은 지역입니다. --> {location}").error
        case region_urls:
            match ex_urls:
                case None:
                    return Err(f"{location} 지역에 등록되지 않은 거래소입니다. --> {market} ({type_})").error
                case dict():
                    match response_url:
                        case None:
                            return Err(f"등록되지 않은 URI 입니다. --> {market} ({type_})").error
                        case _:
                            return Ok(response_url).value
