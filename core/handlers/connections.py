import logging
from typing import Any

logger = logging.getLogger("websocket_handler")


async def handle_connection_event(data: dict[str, Any]) -> None:
    """연결 이벤트 처리 핸들러"""
    exchange: str = data.get("exchange", "unknown")
    status: str = data.get("status", "unknown")
    logger.info(f"[{exchange}] 연결 상태 변경: {status}")


async def handle_error(data: dict[str, Any]) -> None:
    """오류 이벤트 처리 핸들러"""
    exchange: str = data.get("exchange", "unknown")
    error = data.get("error", "unknown")
    logger.error(f"[{exchange}] 오류 발생: {error}")
