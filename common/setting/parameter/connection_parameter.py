from __future__ import annotations

from typing import Any
from common.setting.properties import get_symbol_collect_url
from common.setting.parameter.socket_parameter import create_socket_parameter_from_yaml


class ConnectionParams:
    """웹소켓 연결에 필요한 파라미터를 구성하는 빌더 클래스"""

    def __init__(self, cl: bool) -> None:
        """파라미터 초기화"""
        self._cl: bool = cl
        self._exchange: str = ""
        self._region: str = ""
        self._req_type: str = ""
        self._stream_type: str = ""
        self._symbol: str = ""
        self._timeout: int = 30

    def region(self, region: str) -> ConnectionParams:
        """지역 정보 설정"""
        self._region = region
        return self

    def exchange(self, exchange: str) -> ConnectionParams:
        """거래소 이름 설정"""
        self._exchange = exchange
        return self

    def request_type(self, req_type: str) -> ConnectionParams:
        """요청 타입 설정"""
        self._req_type = req_type
        return self

    def stream_type(self, stream_type: str) -> ConnectionParams:
        """스트림 타입 설정 (socket, rest)"""
        self._stream_type = stream_type
        return self

    def symbol(self, symbol: str) -> ConnectionParams:
        """코인 심볼 설정"""
        self._symbol = symbol
        return self

    def timeout(self, timeout: int) -> ConnectionParams:
        """연결 타임아웃 설정 (초)"""
        self._timeout = timeout
        return self

    def build(self) -> dict[str, Any]:
        """파라미터를 딕셔너리로 구성

        Returns:
            dict[str, Any]: URL과 소켓 파라미터가 포함된 딕셔너리
        """
        url = get_symbol_collect_url(self._exchange, self._region, self._stream_type)
        socket_parameters = create_socket_parameter_from_yaml(
            self._exchange,
            self._symbol,
            self._req_type,
            self._cl,
        )
        parameter = {
            "url": url,
            "region": self._region,
            "request_type": self._req_type,
            "parameters": socket_parameters,
            "timeout": self._timeout,
        }
        return parameter


def create_connection_params(
    cl: bool,
    region: str,
    exchange: str,
    symbol: list[str],
    timeout: int = 30,
    req_type: str = "ticker",
    stream_type: str = "socket",
) -> ConnectionParams:
    """ConnectionParams를 생성하는 데 필요한 파라미터를 구성"""
    return (
        ConnectionParams(cl=cl)
        .region(region)
        .exchange(exchange)
        .request_type(req_type)
        .stream_type(stream_type)
        .symbol(symbol)
        .timeout(timeout)
    )


def get_exchange_config(exchange_name: str, request_type: str) -> ConnectionParams:
    """거래소 이름과 요청 타입을 받아 적절한 config를 반환"""

    # 거래소별 기본 설정
    exchange_settings: dict[str, dict[str, bool | str]] = {
        "upbit": {"cl": False, "region": "korea", "exchange": "upbit"},
        "bithumb": {"cl": False, "region": "korea", "exchange": "bithumb"},
        "korbit": {"cl": False, "region": "korea", "exchange": "korbit"},
        "coinone": {"cl": True, "region": "korea", "exchange": "coinone"},
        "okx": {"cl": False, "region": "asia", "exchange": "okx"},
        "gateio": {"cl": False, "region": "asia", "exchange": "gateio"},
        "bybit": {"cl": False, "region": "asia", "exchange": "bybit"},
        "binance": {"cl": False, "region": "ne", "exchange": "binance"},
        "kraken": {"cl": False, "region": "ne", "exchange": "kraken"},
    }

    # 거래소별 요청 타입 매핑
    request_type_mapping: dict[str, dict[str, str]] = {
        "kraken": {"orderbook": "book"},  # kraken은 orderbook 대신 book 사용
        "okx": {"orderbook": "book"},  # okx는 orderbook 대신 book 사용
        # 다른 거래소의 특수 요청 타입 매핑도 여기에 추가 가능
    }

    if exchange_name not in exchange_settings:
        raise ValueError(f"지원하지 않는 거래소: {exchange_name}")

    settings = exchange_settings[exchange_name]

    # 거래소별 요청 타입 변환
    mapped_request_type = request_type
    condition: bool = (
        exchange_name in request_type_mapping
        and request_type in request_type_mapping[exchange_name]
    )
    if condition:
        mapped_request_type = request_type_mapping[exchange_name][request_type]

    return create_connection_params(
        cl=settings["cl"],
        region=settings["region"],
        exchange=settings["exchange"],
        symbol=["btc"],
        req_type=mapped_request_type,
    )
