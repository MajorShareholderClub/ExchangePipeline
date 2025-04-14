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


# fmt: off
# ---- 한국 거래소 파라미터 설정 ------
# 업비트, 빗썸, 코빗, 코인원
upbit_config = create_connection_params(cl=False, region="korea", exchange="upbit", symbol=["btc"])
bithumb_config = create_connection_params(cl=False, region="korea", exchange="bithumb", symbol=["btc"])
korbit_config = create_connection_params(cl=False, region="korea", exchange="korbit", symbol=["btc"])
coinone_config = create_connection_params(cl=True, region="korea", exchange="coinone", symbol=["btc"])

# ---- 아시아 거래소 파라미터 설정 ------
# OKX, Gateio, Bybit
okx_config = create_connection_params(cl=False, region="asia", exchange="okx", symbol=["btc"])
gateio_config = create_connection_params(cl=False, region="asia", exchange="gateio", symbol=["btc"])
bybit_config = create_connection_params(cl=False, region="asia", exchange="bybit", symbol=["btc"])

# ---- 북미/유럽 거래소 파라미터 설정 ------
# Binance, Kraken
binance_config = create_connection_params(cl=False, region="ne", exchange="binance", symbol=["btc"])
kraken_config = create_connection_params(cl=False, region="ne", exchange="kraken", symbol=["btc"])
