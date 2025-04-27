import time
from typing import Any

from .base import BaseSocketParameter


class BinanceSocketParameter(BaseSocketParameter):
    """바이낸스 거래소 웹소켓 파라미터 생성기"""

    def __init__(self):
        super().__init__(exchange="binance", region="ne")

    def create_parameters(self, symbols: list[str], req_type: str) -> dict[str, Any]:
        """바이낸스 전용 파라미터 생성

        Binance WebSocket API에 맞게 형식을 생성합니다.
        - method: SUBSCRIBE 또는 UNSUBSCRIBE
        - params: ["btcusdt@ticker", "ethusdt@ticker"] 형식의 스트림 배열
        - id: 요청 고유 ID
        """
        if req_type not in self.template:
            raise ValueError(f"지원하지 않는 요청 타입: {req_type}")

        # 템플릿에서 기본 구조 복사
        result = dict(self.template[req_type])
        # params 초기화 (필요한 경우)
        if "params" not in result or not isinstance(result["params"], list):
            result["params"] = []

        # id가 없으면 현재 시간 기준으로 생성
        if result.get("id") == "{req_id}":
            result["id"] = int(time.time() * 1000) % 1000000

        # params가 비어있거나 첫 항목이 비어있는 경우, symbols 기반으로 채우기
        stream_suffix = self._get_stream_suffix(req_type)  # ticker, depth 등

        # 각 심볼마다 적절한 스트림 구성
        formatted_streams = []
        for symbol in symbols:
            # 1. 심볼을 소문자로 변환하고 '_' 제거 (BTC_USDT -> btcusdt)
            formatted_symbol = symbol.lower().replace("_", "")
            # 2. 스트림 형식 구성 (예: btcusdt@ticker)
            stream = f"{formatted_symbol}@{stream_suffix}"
            formatted_streams.append(stream)

        # params 필드 업데이트
        result["params"] = formatted_streams

        return result

    def _get_stream_suffix(self, req_type: str) -> str:
        """요청 타입에 따른 스트림 접미사 반환"""
        # 기본 매핑 (필요에 따라 확장 가능)
        suffix_map = {
            "ticker": "ticker",
            "orderbook": "depth",
            "unsubscribe_ticker": "ticker",
            "unsubscribe_orderbook": "depth",
        }
        return suffix_map.get(req_type, "ticker")  # 기본값은 ticker


class KrakenSocketParameter(BaseSocketParameter):
    """크라켄 거래소 웹소켓 파라미터 생성기"""

    def __init__(self):
        super().__init__(exchange="kraken", region="ne")

    def create_parameters(self, symbols: list[str], req_type: str) -> dict[str, Any]:
        if req_type not in self.template:
            raise ValueError(f"지원하지 않는 요청 타입: {req_type}")
        result = dict(self.template[req_type])

        formatted = [f"{s.upper()}/USD" for s in symbols]
        # subscription name 처리 (ticker/book)
        if "subscription" in result and "name" in result["subscription"]:
            result["subscription"]["name"] = (
                "ticker" if "ticker" in req_type else "book"
            )
        # 심볼 목록 치환
        if result["params"]["symbol"] == "{kraken_symbols}":
            result["params"]["symbol"] = formatted
        return result
