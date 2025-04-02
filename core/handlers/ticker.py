# 티커 핸들러
import json
import logging
from typing import Any

logger = logging.getLogger("ticker_handler")


async def handle_ticker(data: dict[str, Any]) -> None:
    """티커 이벤트 처리 핸들러"""
    # 기존 handle_ticker 함수를 비동기로 변환
    exchange: str = data.get("exchange", "unknown")
    ticker_data: dict[str, Any] = data.get("data", {})
    logger.info(
        f"[{exchange}] 티커 수신: {json.dumps(ticker_data, ensure_ascii=False)[:100]}..."
    )
