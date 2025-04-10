"""데이터 전처리 포맷 설계 (리팩터링 버전)"""

from __future__ import annotations
from typing import Any
from decimal import Decimal, ROUND_HALF_UP
from pydantic import BaseModel, Field, field_validator, ValidationError
from common.setting.types import ExchangeResponseData  # 실제 타입에 맞춰 import


# -----------------------------------------------------------------------------
# PriceData: 각 코인 가격 데이터를 다루는 모델
# -----------------------------------------------------------------------------
class PriceData(BaseModel):
    """코인 현재 가격 데이터"""

    opening_price: Decimal | None = Field(default=None, description="코인 시작가")
    trade_price: Decimal | None = Field(default=None, description="코인 시장가")
    max_price: Decimal | None = Field(default=None, description="코인 고가")
    min_price: Decimal | None = Field(default=None, description="코인 저가")
    prev_closing_price: Decimal | None = Field(default=None, description="코인 종가")
    acc_trade_volume_24h: Decimal | None = Field(
        default=None, description="24시간 거래량"
    )

    # 명시적으로 가격 필드만 반올림 처리하도록 지정
    @field_validator(
        "opening_price",
        "trade_price",
        "max_price",
        "min_price",
        "prev_closing_price",
        "acc_trade_volume_24h",
        mode="before",
    )
    @classmethod
    def round_decimal_fields(cls, value: Any) -> Decimal | None:
        """입력된 값을 Decimal로 변환 후, 0.1 단위로 반올림 (즉, 소수점 한 자리)"""
        if value is None:
            return value
        try:
            # 만약 소수점 셋째 자리 반올림을 원한다면 Decimal("0.001")로 변경
            return Decimal(value).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
        except Exception as e:
            raise ValueError(f"Invalid value for decimal field: {value}") from e


# -----------------------------------------------------------------------------
# CoinMarketData: 코인 마켓 데이터를 다루는 모델
# -----------------------------------------------------------------------------
class CoinMarketData(BaseModel):
    """코인 가격 데이터 스키마

    예시:
    {
        "market": "upbit-BTC",
        "timestamp": 1232355.0,
        "coin_symbol": "BTC",
        "data": {
            "opening_price": 38761000.0,
            "trade_price": 38100000.0,
            "max_price": 38828000.0,
            "min_price": 38470000.0,
            "prev_closing_price": 38742000.0,
            "acc_trade_volume_24h": 2754.0481778
        }
    }
    """

    market: str
    timestamp: float
    coin_symbol: str
    data: PriceData

    @staticmethod
    def _extract_first_value(dictionary: dict[str, Any], key: str) -> Any:
        """
        주어진 dictionary에서 key에 해당하는 값이 리스트면 첫 번째 값을,
        값이 None, 빈 문자열, 혹은 "None"이면 기본값(-1)을 반환.
        """

        if key not in dictionary or dictionary[key] in (None, "", "None"):
            return -1

        value = dictionary[key]
        if isinstance(value, list) and len(value) > 0:
            return value[0]
        return value

    @classmethod
    def _create_price_data(cls, api: dict[str, Any], fields: list[str]) -> PriceData:
        """
        API 데이터에서 PriceData 객체를 생성합니다.
        fields: API에서 각 가격값을 찾아오기 위한 키 리스트 순서대로
                [opening_price, max_price, min_price, trade_price, prev_closing_price, acc_trade_volume_24h]
        """
        return PriceData(
            opening_price=cls._extract_first_value(api, fields[0]),
            max_price=cls._extract_first_value(api, fields[1]),
            min_price=cls._extract_first_value(api, fields[2]),
            trade_price=cls._extract_first_value(api, fields[3]),
            prev_closing_price=cls._extract_first_value(api, fields[4]),
            acc_trade_volume_24h=cls._extract_first_value(api, fields[5]),
        )

    @classmethod
    def from_api(
        cls,
        market: str,
        coin_symbol: str,
        time: float | int,
        api: ExchangeResponseData,
        fields: list[str],
    ) -> CoinMarketData:
        """
        API 데이터를 기반으로 CoinMarketData를 생성합니다.
        :param market: 거래소 및 코인 식별자 문자열
        :param coin_symbol: 코인 심볼 (예: "BTC")
        :param time: 타임스탬프 (float 혹은 int)
        :param api: 원시 API 응답 데이터 (dict 형태)
        :param fields: API 데이터에서 가격 값을 얻기 위한 키 리스트
        """
        price_data = cls._create_price_data(api=api, fields=fields)
        return cls(
            market=market,
            coin_symbol=coin_symbol,
            timestamp=float(time),
            data=price_data,
        )


# -----------------------------------------------------------------------------
# CoinMarketValidationBase: 거래소 데이터 검증 및 초기화 베이스 클래스
# -----------------------------------------------------------------------------
class CoinMarketValidationBase(BaseModel):
    """공통된 거래소 데이터 검증 및 초기화를 제공하는 베이스 클래스"""

    def __init__(self, **data: Any) -> None:
        # 각 거래소 데이터에 대해 개별 검증을 수행합니다.
        validated_data = {
            key: self.validate_exchange_data(value) for key, value in data.items()
        }
        super().__init__(**validated_data)

    @staticmethod
    def validate_exchange_data(value: Any) -> CoinMarketData | bool:
        """
        value가 유효한 API 데이터이면 CoinMarketData로 변환하고,
        아니면 False를 반환합니다.
        """
        try:
            return CoinMarketData.model_validate(value)
        except ValidationError:
            return False


# -----------------------------------------------------------------------------
# 거래소별 데이터 모델들
# -----------------------------------------------------------------------------
class KoreaCoinMarket(CoinMarketValidationBase):
    """한국 거래소 데이터 모델"""

    upbit: CoinMarketData | bool
    bithumb: CoinMarketData | bool
    coinone: CoinMarketData | bool
    korbit: CoinMarketData | bool


class AsiaCoinMarket(CoinMarketValidationBase):
    """해외 거래소 데이터 모델 (아시아 지역)"""

    okx: CoinMarketData | bool
    bybit: CoinMarketData | bool
    gateio: CoinMarketData | bool


class NECoinMarket(CoinMarketValidationBase):
    """해외 거래소 데이터 모델 (북미 등 지역)"""

    binance: CoinMarketData | bool
    kraken: CoinMarketData | bool
