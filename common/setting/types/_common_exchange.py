from typing import TypedDict, TypeVar, Generic, Union, Any, TYPE_CHECKING

# 순환 참조 방지를 위한 조건부 임포트
if TYPE_CHECKING:
    from adapters.exchange import WorldWebSocket
else:
    WorldWebSocket = Any  # 런타임에는 Any 타입으로 처리

T = TypeVar("T")  # 성공 타입
E = TypeVar("E")  # 오류 타입


class Ok(Generic[T]):
    def __init__(self, value: T) -> None:
        self.value = value


class Err(Generic[E]):
    def __init__(self, error: E) -> None:
        self.error = error


Result = Union[Ok[T], Err[E]]


# 각 지역에 대한 URL 구조 정의
class KoreaRegionURLs(TypedDict):
    upbit: str
    bithumb: str
    korbit: str
    coinone: str


class AsiaRegionURLs(TypedDict):
    okx: str
    gateio: str
    bybit: str


class NERegionURLs(TypedDict):
    binance: str
    kraken: str


# 전체 URL 구조 정의
class URLs(TypedDict):
    korea: KoreaRegionURLs
    asia: AsiaRegionURLs
    ne: NERegionURLs


class ExchangeMetadata(TypedDict):
    region: str
    url: str
    exchange_name: str
    request_type: str


class ExchangeSocketParameter(TypedDict):
    """거래소 소켓 파라미터"""

    coin_symbol: str
    metadata: ExchangeMetadata
    parameter_info: dict | list[dict]
    socket_instance: (
        WorldWebSocket  # 실제로는 type[WorldWebSocket] 이지만 순환 참조 방지
    )
