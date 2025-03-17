from typing import Callable, Any, Protocol
from dataclasses import dataclass
import asyncio

from adapters.base.connection import ConnectionManager, exceptions_to_catch

MarketEnv = dict[str, dict[str, Any]]


# 프로토콜 정의 (인터페이스 역할)
class WebSocketAPI(Protocol):
    """웹소켓 API에 필요한 메서드를 정의하는 프로토콜"""

    async def price_present_websocket(self, symbol: str) -> None: ...
    async def orderbook_present_websocket(self, symbol: str) -> None: ...


@dataclass
class WebSocketConfig:
    """웹소켓 클라이언트 설정을 위한 데이터 클래스"""

    symbol: str
    market: str = "all"
    market_env: MarketEnv


# 단일 추상화 계층
@dataclass
class WebSocketClient(ConnectionManager[list[Callable]]):
    """암호화폐 시장 데이터를 위한 기본 웹소켓 클라이언트"""

    config: WebSocketConfig
    _websocket_selector: Callable[[WebSocketAPI], Callable]

    async def _get_websocket_tasks(self) -> list[Callable]:
        """시장 선택에 따른 웹소켓 호출 결과 리스트 반환"""

        if self.config.market == "all":
            # 모든 시장에 대한 웹소켓 호출
            return [
                self._websocket_selector(market_config["api"])(self.config.symbol)
                for _, market_config in self.config.market_env.items()
            ]
        else:
            # 특정 시장에 대한 웹소켓 호출
            if self.config.market not in self.config.market_env:
                raise ValueError(f"시장 '{self.config.market}'이 시장 환경에 없습니다")

            market_config = self.config.market_env[self.config.market]
            return [self._websocket_selector(market_config["api"])(self.config.symbol)]

    async def connect(self, **kwargs) -> list[Callable]:
        """웹소켓 연결 수립"""
        try:
            return await self._get_websocket_tasks()
        except exceptions_to_catch as e:
            self.logger.error(f"웹소켓 연결 수립 중 오류 발생: {e}")
            raise

    async def disconnect(self, connection: list[Callable]) -> None:
        """웹소켓 연결 종료"""
        self.logger.info("웹소켓 연결 종료")
        pass

    async def is_connected(self, connection: list[Callable]) -> bool:
        """웹소켓 연결 상태 확인"""
        return bool(connection)

    async def start(self) -> None:
        """웹소켓 연결 시작 및 데이터 수집"""
        try:
            coroutines = await self.connect()
            if not coroutines:
                raise ValueError("웹소켓 코루틴이 생성되지 않았습니다")
            await asyncio.gather(*coroutines, return_exceptions=False)
        except exceptions_to_catch as e:
            self.logger.error(f"웹소켓 클라이언트 오류: {e}")
            # 재연결 시도 로직 추가 가능
            raise


# 구체적인 클라이언트 구현 (팩토리 함수 사용)
async def create_price_websocket_client(config: WebSocketConfig) -> WebSocketClient:
    """가격 웹소켓 클라이언트 생성

    Args:
        config: 가격 웹소켓 클라이언트 설정

    Returns:
        WebSocketClient: 생성된 웹소켓 클라이언트
    """
    config_socket = WebSocketConfig(
        symbol=config.symbol,
        market_env=config.market_env,
        market=config.market,
    )
    return WebSocketClient(
        config=config_socket,
        _websocket_selector=lambda api: api.price_present_websocket,
    )


async def create_orderbook_websocket_client(config: WebSocketConfig) -> WebSocketClient:
    """호가창 웹소켓 클라이언트 생성

    Args:
        config: 호가창 웹소켓 클라이언트 설정

    Returns:
        WebSocketClient: 생성된 웹소켓 클라이언트
    """
    config_socket = WebSocketConfig(
        symbol=config.symbol,
        market_env=config.market_env,
        market=config.market,
    )
    return WebSocketClient(
        config=config_socket,
        _websocket_selector=lambda api: api.orderbook_present_websocket,
    )
