"""데이터 전처리 포맷 설계"""

from __future__ import annotations
from typing import Any
from decimal import Decimal, ROUND_HALF_UP
from pydantic import BaseModel, field_validator, Field
from common.core.types import ExchangeResponseData


class PriceData(BaseModel):
    """코인 현재 가격 데이터"""

    opening_price: Decimal | None = Field(default=None, description="코인 시작가")
    trade_price: Decimal | None = Field(default=None, description="코인 시장가")
    max_price: Decimal | None = Field(default=None, description="코인 고가")
    min_price: Decimal | None = Field(default=None, description="코인저가")
    prev_closing_price: Decimal | None = Field(default=None, description="코인 종가")
    acc_trade_volume_24h: Decimal | None = Field(
        default=None, description="24시간 거래량"
    )

    @field_validator("*", mode="before")
    @classmethod
    def round_three_place_adjust(cls, value: float) -> Decimal | None:
        """모든 필드에 대한 값을 소수점 셋째 자리로 반올림"""
        if value is None:
            return None
        if isinstance(value, (float, int, str, Decimal)):
            return Decimal(value).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)


class CoinMarketData(BaseModel):
    """Coin price data schema
    Returns:
        >>>  {
                "market": "upbit-BTC",
                "timestamp": 1232355.0,
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
    timestamp: float
    coin_symbol: str
    data: PriceData

    @classmethod
    def _create_price_data(cls, api: dict[str, Any], data: list[str]) -> PriceData:
        """API 데이터에서 PriceData 객체 생성"""
        return PriceData(
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
        time: float | int,
        api: ExchangeResponseData,
        data: list[str],
    ) -> CoinMarketData:
        """API 데이터로부터 CoinMarketData 생성"""
        if isinstance(time, (float, int)):
            timestamp = float(time)
        else:
            raise ValueError("유효하지 않은 타임스탬프입니다.")

        price_data: PriceData = cls._create_price_data(api=api, data=data)
        return cls(
            market=market,
            coin_symbol=coin_symbol,
            timestamp=timestamp,
            data=price_data,
        )


class KoreaCoinMarket(BaseModel):
    """한국 거래소 데이터 모델"""

    upbit: CoinMarketData | bool
    bithumb: CoinMarketData | bool
    coinone: CoinMarketData | bool
    korbit: CoinMarketData | bool


class ForeignCoinMarket(BaseModel):
    """해외 거래소 데이터 모델"""

    binance: CoinMarketData | bool
    kraken: CoinMarketData | bool
    okx: CoinMarketData | bool
    gateio: CoinMarketData | bool
    htx: CoinMarketData | bool
    coinbase: CoinMarketData | bool
