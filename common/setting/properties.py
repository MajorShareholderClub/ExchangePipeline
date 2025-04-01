import configparser
from pathlib import Path
from common.setting.types import (
    URLs,
    KoreaRegionURLs,
    AsiaRegionURLs,
    NERegionURLs,
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
ACKS = parser.get("KAFKA", "acks")


# URL 관리 클래스
class ExchangeURLManager:
    """거래소 URL 관리 클래스

    거래소 URL을 지역 및 유형별로 관리하고 조회하는 기능을 제공합니다.
    40개 이상의 거래소 연결 확장성을 고려하여 구현되었습니다.
    """

    def __init__(self, config_parser: configparser.ConfigParser | None = None):
        """ExchangeURLManager 초기화

        Args:
            config_parser: 설정 파서 객체 (기본값: None, None일 경우 전역 parser 사용)
        """
        self.parser = config_parser or parser

    def get_exchange_urls(self, uri_type: str) -> URLs:
        """모든 거래소 URL 정보를 반환합니다.

        Args:
            uri_type (str): URL 종류 (socket, rest)

        Returns:
            URLs: URL 정보 (socket, rest)
        """
        return URLs(
            korea=KoreaRegionURLs(
                upbit=self.parser.get(f"{uri_type}URL", "UPBIT"),
                bithumb=self.parser.get(f"{uri_type}URL", "BITHUMB"),
                korbit=self.parser.get(f"{uri_type}URL", "KORBIT"),
                coinone=self.parser.get(f"{uri_type}URL", "COINONE"),
            ),
            asia=AsiaRegionURLs(
                okx=self.parser.get(f"{uri_type}URL", "OKX"),
                gateio=self.parser.get(f"{uri_type}URL", "GATEIO"),
                bybit=self.parser.get(f"{uri_type}URL", "BYBIT"),
            ),
            ne=NERegionURLs(
                binance=self.parser.get(f"{uri_type}URL", "BINANCE"),
                kraken=self.parser.get(f"{uri_type}URL", "KRAKEN"),
            ),
        )

    def get_symbol_collect_url(
        self, market: str, location: str, url_type: str
    ) -> Result[Ok[str], Err[str]]:
        """특정 거래소와 지역에 대한 URL을 반환합니다.

        Args:
            market (str): 거래소 이름
            location (str): 지역 정보
            url_type (str): URL 종류 (socket, rest)

        Returns:
            Result[Ok[str], Err[str]]: 매칭된 URL (성공, 실패)
        """
        # location에 해당하는 딕셔너리 가져오기
        urls: URLs = self.get_exchange_urls(url_type.upper())
        region_urls: dict[str, str] = urls.get(location)

        # 1. 지역 URL이 존재하는지 확인
        if not region_urls:
            return Err(f"지역이 등록되지 않았습니다: {location}").error

        # 2. 거래소 URL이 존재하는지 확인
        ex_urls: str | None = region_urls.get(market)
        if not ex_urls:
            return Err(
                f"{location} 지역에서 등록되지 않은 거래소입니다: {market}"
            ).error

        # 3. 모든 조건이 만족되면 URI 반환
        return Ok(ex_urls).value

    def get_region_urls(self, region: str, uri_type: str) -> dict[str, str]:
        """특정 지역의 모든 거래소 URL을 반환합니다.

        Args:
            region (str): 지역 이름 (korea, asia, ne)
            uri_type (str): URL 종류 (socket, rest)

        Returns:
            dict[str, str]: 해당 지역의 거래소 URL 정보
        """
        urls = self.get_exchange_urls(uri_type.upper())
        return getattr(urls, region, {})


# 싱글톤 인스턴스 생성
url_manager = ExchangeURLManager()


def get_symbol_collect_url(
    market: str, location: str, url_type: str
) -> Result[Ok[str], Err[str]]:
    return url_manager.get_symbol_collect_url(market, location, url_type)


def get_all_urls(url_type: str) -> URLs:
    """특정 종류의 모든 거래소 URL을 반환합니다.

    Args:
        url_type (str): URL 종류 (socket, rest)

    Returns:
        URLs: URL 정보 (socket, rest)
    """
    return url_manager.get_exchange_urls(url_type.upper())
