from typing import Callable, Any, Protocol
import asyncio

MarketEnv = dict[str, dict[str, Any]]


# 프로토콜 정의 (인터페이스 역할)
class WebSocketAPI(Protocol):
    """웹소켓 API에 필요한 메서드를 정의하는 프로토콜"""

    async def price_present_websocket(self, symbol: str) -> None: ...
    async def orderbook_present_websocket(self, symbol: str) -> None: ...


# 단일 추상화 계층
class WebSocketClient:
    """암호화폐 시장 데이터를 위한 기본 웹소켓 클라이언트"""

    def __init__(
        self,
        symbol: str,
        market_env: MarketEnv,
        market: str = "all",
        websocket_method_selector: Callable[[WebSocketAPI], Callable] = None,
    ) -> None:
        """웹소켓 클라이언트 초기화

        Args:
            symbol: 데이터를 가져올 암호화폐 심볼
            market_env: 시장 환경 설정
            market: 대상 시장(들). "all"을 사용하여 모든 거래소 선택.
            websocket_method_selector: 웹소켓 메서드 선택 함수
        """
        self.market = market
        self.symbol = symbol
        self.market_env = market_env
        self._websocket_method_selector = websocket_method_selector

        if self._websocket_method_selector is None:
            raise ValueError("웹소켓 메서드 선택자가 필요합니다")

    async def _create_coroutines(self) -> list[Callable]:
        """시장 선택에 따른 웹소켓 코루틴 생성"""
        coroutines = []

        if self.market == "all":
            # 모든 시장에 대한 코루틴 생성
            for market_name, market_config in self.market_env.items():
                websocket_method = self._websocket_method_selector(market_config["api"])
                coroutines.append(websocket_method(self.symbol))
        else:
            # 특정 시장에 대한 코루틴 생성
            if self.market not in self.market_env:
                raise ValueError(f"시장 '{self.market}'이 시장 환경에 없습니다")

            market_config = self.market_env[self.market]
            websocket_method = self._websocket_method_selector(market_config["api"])
            coroutines.append(websocket_method(self.symbol))

        return coroutines

    async def start(self) -> None:
        """웹소켓 연결 시작 및 데이터 수집"""
        try:
            coroutines = await self._create_coroutines()
            if not coroutines:
                raise ValueError("웹소켓 코루틴이 생성되지 않았습니다")

            await asyncio.gather(*coroutines, return_exceptions=False)
        except Exception as e:
            # 오류 로깅 및 재발생
            print(f"웹소켓 클라이언트 오류: {e}")
            raise


# 구체적인 클라이언트 구현 (팩토리 함수 사용)
def create_price_websocket_client(
    symbol: str,
    market_env: MarketEnv,
    market: str = "all",
) -> WebSocketClient:
    """가격 웹소켓 클라이언트 생성"""
    return WebSocketClient(
        symbol=symbol,
        market_env=market_env,
        market=market,
        websocket_method_selector=lambda api: api.price_present_websocket,
    )


def create_orderbook_websocket_client(
    symbol: str,
    market_env: MarketEnv,
    market: str = "all",
) -> WebSocketClient:
    """호가창 웹소켓 클라이언트 생성"""
    return WebSocketClient(
        symbol=symbol,
        market_env=market_env,
        market=market,
        websocket_method_selector=lambda api: api.orderbook_present_websocket,
    )
