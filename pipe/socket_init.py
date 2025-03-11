import asyncio
from typing import Union
from pipe.connection import CoinOrderBookWebsocket, CoinPresentPriceWebsocket

# 타입 힌트 개선
# Union 형태로 명시적 표현
ConnectionType = Union[CoinOrderBookWebsocket, CoinPresentPriceWebsocket]


async def run_coin_websocket(
    connection_class: ConnectionType, symbol: str, location: str
) -> None:
    """지정된 웹소켓 클라이언트로 시장 데이터 수집

    Args:
        connection_class: 웹소켓 연결 클래스
        symbol: 암호화폐 심볼 (예: BTC)
        location: 지역 위치 (예: korea, asia, ne)

    Returns:
        None
    """
    websocket_client = connection_class(symbol=symbol, location=location, market="all")
    await websocket_client.start()


async def coin_present_websocket(connection_class: ConnectionType) -> None:
    """여러 지역의 코인 웹소켓을 동시에 실행

    스레드풀 대신 asyncio.create_task를 사용하여 비동기 작업 관리

    Args:
        connection_class: 웹소켓 연결 클래스

    Returns:
        None
    """
    # 지역 목록 정의
    locations = ["korea", "asia", "ne"]
    symbol = "BTC"  # 상수를 변수로 분리하여 가독성 향상

    # 각 지역별 태스크 생성
    tasks = [
        run_coin_websocket(connection_class, symbol, location) for location in locations
    ]

    # 모든 태스크 동시 실행
    await asyncio.gather(*tasks, return_exceptions=False)


if __name__ == "__main__":
    asyncio.run(coin_present_websocket(CoinOrderBookWebsocket))
