import json
from typing import Any
from common.logger import PipelineLogger


async def handle_ticker(data: dict[str, Any]) -> None:
    """티커 이벤트 처리 핸들러"""
    # 기존 handle_ticker 함수를 비동기로 변환
    exchange: str = data.get("exchange", "unknown")
    ticker_data: dict[str, Any] = data.get("data", {})

    print(exchange, ticker_data)
