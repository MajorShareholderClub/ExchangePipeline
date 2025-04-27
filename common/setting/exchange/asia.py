import time
from typing import Any
import uuid

from .base import BaseSocketParameter


class GateioSocketParameter(BaseSocketParameter):
    """게이트아이오 거래소 웹소켓 파라미터 생성기"""

    def __init__(self):
        super().__init__(exchange="gateio", region="asia")

    def create_parameters(self, symbols: list[str], req_type: str) -> dict[str, Any]:
        """게이트아이오 전용 파라미터 생성 (ticker, orderbook, unsubscribe 지원)"""
        if req_type not in self.template:
            raise ValueError(f"지원하지 않는 요청 타입: {req_type}")

        result = dict(self.template[req_type])
        # time 필드는 항상 현재 시간으로 치환
        if "time" in result:
            result["time"] = int(time.time())

        # payload 치환 (티커: 심볼 리스트, 오더북: [[심볼, depth, interval], ...])
        if "payload" in result:
            if req_type.startswith("ticker") or req_type.startswith(
                "unsubscribe_ticker"
            ):
                result["payload"] = [f"{s}_USDT" for s in symbols]
            elif req_type.startswith("orderbook") or req_type.startswith(
                "unsubscribe_orderbook"
            ):
                # list comprehension으로 변환
                result["payload"] = [[s, 20, 100] for s in symbols]
        return result


class OkxSocketParameter(BaseSocketParameter):
    """OKX 거래소 웹소켓 파라미터 생성기"""

    def __init__(self):
        super().__init__(exchange="okx", region="asia")

    def create_parameters(self, symbols: list[str], req_type: str) -> dict[str, Any]:
        """OKX 전용 파라미터 생성 (ticker, orderbook, unsubscribe 지원)"""
        if req_type not in self.template:
            raise ValueError(f"지원하지 않는 요청 타입: {req_type}")

        result = dict(self.template[req_type])

        # args 치환: channel/instId (list comprehension 적용)
        if "args" in result and isinstance(result["args"], list):
            channel = "tickers" if "ticker" in req_type else "books"
            result["args"] = [
                {"channel": channel, "instId": f"{s.upper().replace("_", "-")}-USDT"}
                for s in symbols
            ]
        return result


class BybitSocketParameter(BaseSocketParameter):
    """Bybit 거래소 웹소켓 파라미터 생성기"""

    def __init__(self):
        super().__init__(exchange="bybit", region="asia")

    def create_parameters(self, symbols: list[str], req_type: str) -> dict[str, Any]:
        """Bybit 전용 파라미터 생성 (ticker, orderbook, unsubscribe 지원)"""
        if req_type not in self.template:
            raise ValueError(f"지원하지 않는 요청 타입: {req_type}")
        result = dict(self.template[req_type])

        def bybit_arg(req_type: str, symbol: str) -> str:
            match req_type:
                case t if "ticker" in t:
                    return f"tickers.{symbol.replace('_', '').upper()}USDT"
                case t if "orderbook" in t:
                    return f"orderbook.50.{symbol.replace('_', '').upper()}USDT"
                case _:
                    return symbol

        # req_id 치환
        if "req_id" in result:
            result["req_id"] = str(uuid.uuid4())

        if "args" in result:
            result["args"] = [bybit_arg(req_type, s) for s in symbols]
        return result
