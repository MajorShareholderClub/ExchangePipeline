from typing import Any
from messaging.data_interaction import KafkaMessageSender


async def handle_ticker(data: dict[str, Any]) -> None:
    """티커 이벤트 처리 핸들러"""

    # 기존 handle_ticker 함수를 비동기로 변환
    exchange: str = data.get("exchange", "unknown")
    response_type: str = data.get("response_type", "unknown")
    ticker_data: dict[str, Any] = data.get("data", {})

    symbol = list(ticker_data.keys())[0]

    key = f"{exchange}::{response_type}-{ticker_data[symbol]}"

    sender = KafkaMessageSender()
    await sender.produce_sending(message=ticker_data, topic="ticker", key=key)
