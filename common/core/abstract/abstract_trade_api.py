"""대한민국 거래소 그리고 해외거래소 통합 추상 클래스"""

from typing import Callable
from typing import Coroutine, Any
from abc import abstractmethod, ABC
from common.core.types import ExchangeResponseData
from common.setting.properties import get_symbol_collect_url
from common.core.types import SubScribeFormat


# Rest
class AbstractExchangeRestClient(ABC):
    def __init__(self, market: str, location: str) -> None:
        self._rest = get_symbol_collect_url(
            market=market, type_="rest", location=location
        )

    @abstractmethod
    async def get_coin_all_info_price(self, coin_name: str) -> ExchangeResponseData:
        """
        Subject:
            - 코인 인덱스 가격 정보 \n
        Parameter:
            - coin_name (str) : 코인이름\n
        Returns:
            - market 형식
        """
        raise NotImplementedError()


# Socket
class AbstractExchangeSocketClient(ABC):
    def __init__(
        self,
        target: str,
        location: str,
        socket_parameter: Callable[[str], SubScribeFormat],
    ) -> None:
        self._websocket = get_symbol_collect_url(target, "socket", location)
        self.socket_parameter = socket_parameter
        self.ticker = "ticker"
        self.orderbook = "orderbook"

    @abstractmethod
    async def get_present_websocket(
        self, symbol: str, req_type: str, socket_type: str
    ) -> Coroutine[Any, Any, None]:
        """
        Subject:
            - 코인 현재가 실시간 \n
        Args:
            - uri (str): 소켓주소
            - subscribe_fmt (list[dict]): 인증파라미터 \n
            - symbol (str) : 심볼
        Returns:
            - 무한루프 \n
        """
        raise NotImplementedError()
