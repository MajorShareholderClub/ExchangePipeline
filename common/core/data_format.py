"""데이터 전처리 포맷 설계"""

from __future__ import annotations
from typing import Any
from decimal import Decimal, ROUND_HALF_UP
from pydantic import BaseModel, field_validator, ValidationError, Field


class BaseCoinMarket(BaseModel):

    timestamp: int

    def __init__(self, **data: KoreaCoinMarket) -> None:
        # 우선 timestamp 추출
        timestamp = data.pop("timestamp", None)

        # 거래소 데이터 검증 및 할당
        exchange_data: dict[str, CoinMarketData | bool] = {
            key: self.validate_exchange_data(value) for key, value in data.items()
        }
        # 합쳐진 데이터를 사용하여 부모 클래스 초기화
        super().__init__(timestamp=timestamp, **exchange_data)

    @staticmethod
    def validate_exchange_data(value: Any) -> CoinMarketData | bool:
        try:
            return CoinMarketData.model_validate(value)
        except ValidationError:
            return False


class KoreaCoinMarket(BaseModel):
    """
    Subject:
        한국 거래소 모음 : (rest: 4개(업비트, 빗썸, 코인원, 코빗), socket: 3개(코빗 추가되면 4개)
    Returns:
        - pydantic in JSON transformation \n
        >>> {
                "timestamp": 1689633864,
                "upbit": {
                    "name": "upbit-ETH",
                    "coin_symbol": "BTC",
                    "data": {
                        "opening_price": 2455000.0,
                        "trade_price": 38100000.0
                        "max_price": 2462000.0,
                        "min_price": 2431000.0,
                        "prev_closing_price": 2455000.0,
                        "acc_trade_volume_24h": 11447.92825886,
                    }
                },
                ....
            }
    """

    upbit: CoinMarketData | bool
    bithumb: CoinMarketData | bool
    coinone: CoinMarketData | bool
    korbit: CoinMarketData | bool


class ForeignCoinMarket(BaseModel):
    """
    Subject:
        해외거래소 : (바이낸스, 크라켄, okx, gateio, htx(후오비), 코인베이스)
    Returns:
        pydantic in JSON transformation \n
        >>> {
                "timestamp": 1689633864,
                "binance": {
                    "name": "binance-ETH",
                    "coin_symbol": "BTC",
                    "data": {
                        "opening_price": 2455000.0,
                        "trade_price": 38100000.0,
                        "max_price": 2462000.0,
                        "min_price": 2431000.0,
                        "prev_closing_price": 2455000.0,
                        "acc_trade_volume_24h": 11447.92825886
                    }
                },
                ...
            }
    """

    binance: CoinMarketData | bool
    kraken: CoinMarketData | bool
    okx: CoinMarketData | bool
    gateio: CoinMarketData | bool
    htx: CoinMarketData | bool
    coinbase: CoinMarketData | bool


class PriceData(BaseModel):
    """코인 현재 가격가

    Args:
        BaseModel (_type_): pydantic

    Returns:
        _type_: Decimal type
    """

    # ask: Decimal | None = None
    # bid: Decimal | None = None
    opening_price: Decimal | None = Field(default=None, description="시작가")
    trade_price: Decimal | None = Field(default=None, description="시장가")
    max_price: Decimal | None = Field(default=None, description="고가")
    min_price: Decimal | None = Field(default=None, description="저가")
    prev_closing_price: Decimal | None = Field(default=None, description="종료가")
    acc_trade_volume_24h: Decimal | None = Field(
        default=None, description="24시간 거래개수"
    )

    @field_validator("*")
    @classmethod
    def round_three_place_adjust(cls, value: Any) -> Decimal | None:
        if value is None:
            return None
        return Decimal(value).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)


class CoinMarketData(BaseModel):
    """Coin price data schema
    Args:
        - BaseModel (_type_): pydantic BaseModel 으로 구현 했습니다  \n
    Returns:
        >>>  {
                "market": "upbit-BTC",
                "coin_symbol": "BTC",
                "data": {
                    "opening_price": 38761000.0,
                    "trade_price": 38100000.0
                    "high_price": 38828000.0,
                    "low_price": 38470000.0,
                    "prev_closing_price": 38742000.0,
                    "acc_trade_volume_24h": 2754.0481778
                }
            }
    """

    market: str
    coin_symbol: str
    data: PriceData

    # fmt: off
    @classmethod
    def _create_price_data(cls, api: dict[str, int], data: list[str]) -> PriceData:
        return PriceData(
            # ask=api[data[0]],
            # bid=api[data[1]],
            opening_price=api[data[0]],
            max_price=api[data[1]],
            min_price=api[data[2]],
            trade_price=api[data[3]],
            prev_closing_price=api[data[4]],
            acc_trade_volume_24h=api[data[5]],
        )

    @classmethod
    def from_api(
        cls,
        market: str,
        coin_symbol: str,
        api: dict[str, Any],
        data: list[str],
    ) -> CoinMarketData:
        """다음과 같은 dictionary를 만들기 위한 pydantic json model architecture
        >>>  {
            "market": "upbit-BTC",
            "coin_symbol": "BTC",
            "data": {
                "opening_price": 38761000.0,
                "trade_price": 38100000.0
                "high_price": 38828000.0,
                "low_price": 38470000.0,
                "prev_closing_price": 38742000.0,
                "acc_trade_volume_24h": 2754.0481778
            }
        }
        Args:
            market (str): 거래소 이름
            coin_symbol (str): 심볼
            api (Mapping[str, Any]): 거래소 API
            data (list[str, str, str, str, str, str]): 사용할 파라미터 \n
        Returns:
            CoinMarketData: _description_
        """
        price_data: PriceData = cls._create_price_data(api=api, data=data)
        return cls(
            market=market,
            coin_symbol=coin_symbol,
            data=price_data,
        )
