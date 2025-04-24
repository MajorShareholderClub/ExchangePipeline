import time
import uuid

from typing import Any, Callable, TypedDict
from common.setting.config.yml_config import template_config


class MappingDict(TypedDict):
    uuid: str
    req_type: str
    time: int
    symbol_upper: str
    symbol_lower: str
    symbol_code_list: list[str]
    symbol_list: list[str]
    binance_params: list[str]
    kraken_symbols: list[str]
    gateio_payload: list[str]
    bybit_args: list[str]
    okx_args: list[dict[str, str]]


class SocketParameterBuilder:
    """소켓 파라미터를 생성하는 빌더 클래스"""

    def __init__(
        self,
        exchange: str,
        symbols: list[str] | str,
        req_type: str,
        cl: bool = True,
    ) -> None:
        """
        소켓 파라미터 빌더 초기화

        Args:
            exchange: 거래소 이름
            symbols: 코인 심볼 리스트 또는 단일 심볼
            req_type: 요청 타입
            cl: 대소문자 구분 플래그
        """
        self.exchange = exchange.lower()
        self.symbols = symbols if isinstance(symbols, list) else [symbols]
        self.req_type = req_type.upper() if cl else req_type.lower()
        self.cl = cl
        self.templates = template_config()

        if self.exchange not in self.templates:
            raise KeyError(f"등록되지 않은 거래소입니다: {exchange}")

    def map_symbols(self, formatter: Callable[[str], str]) -> list[str]:
        """심볼 리스트를 받아 formatter 함수에 따라 변환한 새 리스트를 반환합니다."""
        return [formatter(s) for s in self.symbols]

    def build_mapping(self) -> MappingDict:
        """매핑 딕셔너리 생성"""

        # 바이낸스 파라미터 형식 결정
        def get_binance_param(symbol: str) -> str:
            symbol_lower = symbol.lower()
            if self.req_type.lower() == "orderbook":
                # 오더북인 경우 depth 형식 사용 (전체 오더북은 @depth, 상위 10개 호가는 @depth10)
                return f"{symbol_lower}usdt@depth"
            else:
                # 그 외(ticker 등)는 기존 형식 유지
                return f"{symbol_lower}usdt@{self.req_type}"

        return MappingDict(
            uuid=str(uuid.uuid4()),
            req_type=self.req_type,
            time=int(time.time()),
            # 첫번째 코인 관련 정보 (필요시)
            symbol_upper=self.symbols[0].upper(),
            symbol_lower=self.symbols[0].lower(),
            # 각 거래소별 다중 코인 처리를 위한 리스트 치환
            symbol_code_list=self.map_symbols(lambda s: f"KRW-{s.upper()}"),
            symbol_list=self.map_symbols(lambda s: f"{s.lower()}_krw"),
            binance_params=self.map_symbols(get_binance_param),
            kraken_symbols=self.map_symbols(lambda s: f"{s.upper()}/USD"),
            gateio_payload=self.map_symbols(lambda s: f"{s.upper()}_USDT"),
            bybit_args=self.map_symbols(lambda s: f"{self.req_type}s.{s.upper()}USDT"),
            okx_args=self.map_symbols(
                lambda s: {
                    "channel": f"{self.req_type}s",
                    "instId": f"{s.upper()}-USDT",
                }
            ),
        )

    def substitute_placeholders(
        self, value: Any, mapping: dict[str, Any]
    ) -> str | dict | list:
        """
        재귀적으로 value 내부의 문자열 내 플레이스홀더를 mapping의 값으로 치환.
        - 문자열: .format(**mapping) 사용
        - 딕셔너리: 하위 값에 대해 재귀 호출
        - 리스트: 각 요소에 대해 재귀 호출
        - 그 외: 그대로 반환
        """
        match value:
            case str():
                if (
                    value.startswith("{")
                    and value.endswith("}")
                    and value.count("{") == 1
                ):
                    key = value[1:-1]
                    if key in mapping:
                        return mapping[key]
                return value.format(**mapping)
            case dict():
                return {
                    k: self.substitute_placeholders(v, mapping)
                    for k, v in value.items()
                }
            case list():
                return [self.substitute_placeholders(item, mapping) for item in value]
            case _:
                return value

    def build(self) -> dict:
        """소켓 파라미터 생성"""
        mapping: MappingDict = self.build_mapping()
        template = self.templates[self.exchange]
        return self.substitute_placeholders(template, mapping)


def create_socket_parameter_from_yaml(
    exchange: str,
    symbols: list[str] | str,
    req_type: str,
    cl: bool = True,
) -> dict:
    """
    지정한 거래소, 다중 코인(symbol 리스트) 및 요청 타입(req_type)에 대해 YAML 템플릿을 기반으로
    소켓 파라미터를 생성합니다.
    """
    builder = SocketParameterBuilder(exchange, symbols, req_type, cl)
    return builder.build()
