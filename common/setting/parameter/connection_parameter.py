from __future__ import annotations

from typing import Any
from common.setting.properties import get_symbol_collect_url
from common.setting.parameter.socket_parameter import create_socket_parameter


class ConnectionParams:
    """웹소켓 연결에 필요한 파라미터를 구성하는 빌더 클래스"""

    def __init__(self) -> None:
        """파라미터 초기화"""
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
        socket_parameters = create_socket_parameter(
            self._exchange, self._symbol, self._req_type
        )
        parameter = {
            "url": url,
            "parameters": socket_parameters,
            "timeout": self._timeout,
        }
        return parameter


# 업비트 설정
upbit_config = (
    ConnectionParams()
    .region("korea")
    .exchange("upbit")
    .request_type("ticker")
    .stream_type("socket")
    .symbol("btc")
    .timeout(30)
)

# 빗썸 설정
bithumb_config = (
    ConnectionParams()
    .region("korea")
    .exchange("bithumb")
    .request_type("ticker")
    .stream_type("socket")
    .symbol("btc")
    .timeout(30)
)

# 코빗 설정
korbit_config = (
    ConnectionParams()
    .region("korea")
    .exchange("korbit")
    .request_type("ticker")
    .stream_type("socket")
    .symbol("btc")
    .timeout(30)
)

# 코인원 설정
coinone_config = (
    ConnectionParams()
    .region("korea")
    .exchange("coinone")
    .request_type("ticker")
    .stream_type("socket")
    .symbol("btc")
    .timeout(30)
)

# ---- 아시아 거래소 파라미터 설정 ------

# OKX 설정
okx_config = (
    ConnectionParams()
    .region("asia")
    .exchange("okx")
    .request_type("ticker")
    .stream_type("socket")
    .symbol("btc")
    .timeout(30)
)

# Gateio 설정
gateio_config = (
    ConnectionParams()
    .region("asia")
    .exchange("gateio")
    .request_type("ticker")
    .stream_type("socket")
    .symbol("btc")
    .timeout(30)
)

# Bybit 설정
bybit_config = (
    ConnectionParams()
    .region("asia")
    .exchange("bybit")
    .request_type("ticker")
    .stream_type("socket")
    .symbol("btc")
    .timeout(30)
)

# ---- 북미/유럽 거래소 파라미터 설정 ------

# Binance 설정
binance_config = (
    ConnectionParams()
    .region("ne")
    .exchange("binance")
    .request_type("ticker")
    .stream_type("socket")
    .symbol("btc")
    .timeout(30)
)

# Kraken 설정
kraken_config = (
    ConnectionParams()
    .region("ne")
    .exchange("kraken")
    .request_type("ticker")
    .stream_type("socket")
    .symbol("btc")
    .timeout(30)
)
