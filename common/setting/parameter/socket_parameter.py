import time
from typing import Callable, Any

import uuid
from common.setting.types import (
    UpBithumbSocketParameter,
    TicketUUID,
    CombinedRequest,
    CoinoneSocketParameter,
    CoinoneTopicParameter,
    KorbitSocketParameter,
)
from common.setting.types import (
    BinanceSocketParameter,
    KrakenSocketParameter,
    KrakenParameter,
    GateioSocketParameter,
    OKXArgsSocketParameter,
    OKXSocketParameter,
    BybitSocketParameter,
)

UUID = str(uuid.uuid4())

# fmt: off
def upbithumb_socket_parameter(symbol: str, req_type: str) -> UpBithumbSocketParameter:
    return [
        TicketUUID(ticket=UUID),
        CombinedRequest(
            type=req_type,
            codes=[f"KRW-{symbol.upper()}"],
            is_only_realtime=True,
        )
    ]

def coinone_socket_parameter(symbol: str, req_type: str) -> CoinoneSocketParameter:
    return CoinoneSocketParameter(
        request_type="SUBSCRIBE",
        channel=req_type.upper(),
        topic=CoinoneTopicParameter(
            quote_currency="KRW", target_currency=f"{symbol.upper()}"
        ),
    )

def korbit_socket_parameter(symbol: str, req_type: str) -> list[KorbitSocketParameter]:
    return [
        KorbitSocketParameter(
            method="subscribe",
            type=req_type,
            symbols=[f"{symbol.lower()}_krw"]
        )
    ]

def binance_socket_paramater(symbol: str, req_type: str) -> BinanceSocketParameter:
    return BinanceSocketParameter(
        id=UUID,
        method=f"SUBSCRIBE",
        params=[f"{symbol.lower()}usdt@{req_type}"],
    )

def kraken_socket_parameter(symbol: str, req_type: str) -> KrakenSocketParameter:
    return KrakenSocketParameter(
        method="subscribe",
        params=KrakenParameter(
            channel=f"{req_type}", 
            symbol=[f"{symbol.upper()}/USD"],
            event_trigger="trades",
            snapshot=False
        ),
        req_id=UUID
    )

def gateio_socket_parameter(symbol: str, req_type: str) -> GateioSocketParameter:
    return GateioSocketParameter(
        time=int(time.time()),
        channel=f"spot.{req_type}",
        event="subscribe",
        payload=[f"{symbol.upper()}_USDT"]
    )

def bybit_socket_parameter(symbol: str, req_type: str) -> BybitSocketParameter:
    return BybitSocketParameter(
        req_id=UUID,
        op="subscribe",
        args=[f"{req_type}.{symbol.upper()}USDT"]
    )

def okx_socket_parameter(symbol: str, req_type: str) -> OKXSocketParameter:
    return OKXSocketParameter(
        op="subscribe",
        args=[OKXArgsSocketParameter(channel=req_type, instId=f"{symbol}-USDT")],
    )



# 소켓 파라미터 함수 맵
# 거래소 이름을 키로 해당 거래소의 소켓 파라미터 생성 함수를 가져올 수 있음
SOCKET_PARAMETER_FUNCTIONS = {
    # 한국 지역 거래소
    "upbit": upbithumb_socket_parameter,
    "bithumb": upbithumb_socket_parameter,  
    "korbit": korbit_socket_parameter,
    "coinone": coinone_socket_parameter,
    
    # 아시아 지역 거래소
    "okx": okx_socket_parameter,
    "gateio": gateio_socket_parameter,
    "bybit": bybit_socket_parameter,
    
    # 유럽/미국 지역 거래소
    "binance": binance_socket_paramater,
    "kraken": kraken_socket_parameter,
}



# 소켓 파라미터 생성 함수
def create_socket_parameter(exchange_name: str, symbol: str, req_type: str) -> Any:

    """특정 거래소의 소켓 파라미터를 생성합니다.
    
    Args:
        exchange_name (str): 거래소 이름
        symbol (str): 코인 심볼
        req_type (str): 요청 타입
        
    Returns:
        Any: 거래소에 맞는 소켓 파라미터
    """
    
    # 소켓 파라미터 생성 함수 조회 함수
    def get_socket_parameter_function(exchange_name: str) -> Callable:
        """특정 거래소의 소켓 파라미터 생성 함수를 반환합니다.
        
        Args:
            exchange_name (str): 거래소 이름
            
        Returns:
            callable: 소켓 파라미터 생성 함수
            
        Raises:
            KeyError: 등록되지 않은 거래소일 경우
        """
        try:
            return SOCKET_PARAMETER_FUNCTIONS[exchange_name.lower()]
        except KeyError:
            raise KeyError(f"등록되지 않은 거래소입니다: {exchange_name}")
        
    parameter_function = get_socket_parameter_function(exchange_name)
    return parameter_function(symbol, req_type)
