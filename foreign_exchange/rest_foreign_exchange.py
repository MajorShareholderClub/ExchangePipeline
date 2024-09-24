"""코인 Rest Resquest 설계 (국내)"""

import ccxt
from typing import Coroutine, Any, Any
from common.core.types import ExchangeResponseData
from abc import abstractmethod
from common.core.abstract import AbstractExchangeRestClient


# fmt: off
class CommonForeignMarketRestClient(AbstractExchangeRestClient):
    @abstractmethod
    def get_exchange_instance(self) -> Any:
        """각 거래소 인스턴스를 반환하는 메서드. 각 하위 클래스가 구현해야 함."""
        raise NotImplementedError()

    @abstractmethod
    def get_symbol(self, coin_name: str) -> str:
        """코인 심볼을 각 거래소에 맞게 변환하는 메서드."""
        raise NotImplementedError()

    async def get_coin_all_info_price(self, coin_name: str) -> Coroutine[Any, Any, ExchangeResponseData]:
        markets: ccxt.coinone = self.get_exchange_instance()
        coin: str = self.get_symbol(coin_name=coin_name)
        return markets.fetch_ticker(coin)


class BinanceRest(CommonForeignMarketRestClient):
    def get_exchange_instance(self) -> ccxt.binance:
        """ccxt 바이낸스 REST API 호출"""
        return ccxt.binance()

    def get_symbol(self, coin_name: str) -> str:
        """코인 심볼을 바이낸스 형식으로 변환 (예: BTC/USDT)"""
        return f"{coin_name.upper()}/USDT"


class KrakenRest(CommonForeignMarketRestClient):
    def get_exchange_instance(self) -> ccxt.kraken:
        """ccxt 크라켄 REST API 호출"""
        return ccxt.kraken()

    def get_symbol(self, coin_name: str) -> str:
        """코인 심볼을 크라켄 형식으로 변환 (예: BTC/USD)"""
        return f"{coin_name.upper()}/USDT"


class OKXRest(CommonForeignMarketRestClient):
    def get_exchange_instance(self) -> ccxt.okx:
        """ccxt OKX REST API 호출"""
        return ccxt.okx()

    def get_symbol(self, coin_name: str) -> str:
        """코인 심볼을 OKX 형식으로 변환 (예: BTC/USDT)"""
        return f"{coin_name.upper()}/USDT"


class CoinbaseRest(CommonForeignMarketRestClient):
    def get_exchange_instance(self) -> ccxt.coinbase:
        """ccxt 코인베이스 REST API 호출"""
        return ccxt.coinbase()

    def get_symbol(self, coin_name: str) -> str:
        """코인 심볼을 코인베이스 형식으로 변환 (예: BTC/USD)"""
        return f"{coin_name.upper()}/USDT"


class BybitRest(CommonForeignMarketRestClient):
    def get_exchange_instance(self) -> ccxt.bybit:
        """ccxt 바이비트 REST API 호출"""
        return ccxt.bybit()

    def get_symbol(self, coin_name: str) -> str:
        """코인 심볼을 바이비트 형식으로 변환 (예: BTC/USDT)"""
        return f"{coin_name.upper()}/USDT"


class GateIORest(CommonForeignMarketRestClient):
    def get_exchange_instance(self) -> ccxt.gateio:
        """ccxt GateIO REST API 호출"""
        return ccxt.gateio()

    def get_symbol(self, coin_name: str) -> str:
        """코인 심볼을 GateIO 형식으로 변환 (예: BTC/USDT)"""
        return f"{coin_name.upper()}/USDT"


class HTXRest(CommonForeignMarketRestClient):
    def get_exchange_instance(self) -> ccxt.huobi:
        """ccxt HTX (Huobi) REST API 호출"""
        return ccxt.huobi()

    def get_symbol(self, coin_name: str) -> str:
        """코인 심볼을 HTX 형식으로 변환 (예: BTC/USDT)"""
        return f"{coin_name.upper()}/USDT"
