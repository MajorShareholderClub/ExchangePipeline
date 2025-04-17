from typing import TypedDict, TypeVar, Generic, Union

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
