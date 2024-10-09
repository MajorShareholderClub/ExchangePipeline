from abc import ABC, abstractmethod

import time
import json
import logging
import tracemalloc
from collections import defaultdict

import websockets
import asyncio

from typing import Any, Callable
from config.yml_param_load import RestMarketLoader, SocketMarketLoader

from mq.data_interaction import KafkaMessageSender
from common.core.types import (
    ExchangeData,
    KoreaCoinMarketData,
    SubScribeFormat,
    SocketLowData,
    ExchangeResponseData,
)
from common.core.data_format import CoinMarketData
from common.utils.logger import AsyncLogger
from common.core.abstract import (
    WebsocketConnectionAbstract,
)

socket_protocol = websockets.WebSocketClientProtocol

"""
REST -----------------------------------------------------------------------------------------------------------------------------
"""


# rest
async def schema_create(
    market: str,
    time: int | float,
    symbol: str,
    api: Any,
    data: tuple[str],
):
    return CoinMarketData.from_api(
        market=market,
        coin_symbol=symbol,
        time=time,
        api=api,
        data=data,
    ).model_dump()


class CoinPresentPriceClient:

    def __init__(self, location: str) -> None:
        self.market_env = RestMarketLoader(location).process_market_info()
        self.logging = AsyncLogger(target=location, folder="rest")

    async def _transform_and_request(
        self, market: str, time: int | float, symbol: str, api: Any, data: tuple[str]
    ) -> ExchangeData:
        """스키마 변환 함수"""
        api_response = await api.get_coin_all_info_price(coin_name=symbol.upper())
        if api_response is None:
            return await schema_create(
                market=market, time=time, symbol=symbol, api=None, data=data
            )
        return await schema_create(
            market=market, time=time, symbol=symbol, api=api_response, data=data
        )

    async def _trans_schema(self, market: str, symbol: str) -> ExchangeData:
        """스키마 변환 본체"""
        # try:
        market_info = self.market_env[market]
        market_data_architecture = await self._transform_and_request(
            market=f"{market}-{symbol.upper()}",
            symbol=symbol,
            time=int(time.time()),
            api=market_info["api"],
            data=market_info["parameter"],
        )
        return market_data_architecture


class BaseExchangeRestAPI(CoinPresentPriceClient, ABC):
    """기본 거래소 API"""

    def __init__(self, location: str) -> None:
        super().__init__(location=location)

    async def fetch_market_data(self, symbol: str) -> list[ExchangeData | Exception]:
        """시장 데이터 가져오기"""
        tasks = [
            self._trans_schema(market=market, symbol=symbol)
            for market in self.market_env
        ]
        return await asyncio.gather(*tasks, return_exceptions=True)

    @abstractmethod
    def create_schema(self, market_result: list[ExchangeData]) -> Any:
        """스키마 생성 메서드"""
        raise NotImplementedError("메서드 구현 필수 입니다")

    async def _log_market_schema(self, coin_symbol: str) -> None:
        """공통 로깅 함수"""
        market_result = await self.fetch_market_data(coin_symbol)
        schema: KoreaCoinMarketData = self.create_schema(market_result)
        await self.logging.log_message(logging.INFO, message=schema)

        return schema

    @abstractmethod
    async def total_pull_request(self, coin_symbol: str, interval: int = 1) -> None:
        """Rest 시작점"""
        raise NotImplementedError("메서드 구현 필수 입니다")


"""
Socket -----------------------------------------------------------------------------------------------------------------------------
"""


# socket
class MessageDataPreprocessing:
    def __init__(self, type_: str, location: str) -> None:
        self.market = SocketMarketLoader(location).process_market_info()
        self._logger = AsyncLogger(
            target=f"{type_}_websocket", folder=f"websocket_{location}"
        )
        self.message_by_data = defaultdict(list)
        self.message_async_q = asyncio.Queue()

    async def put_message_to_logging(
        self,
        uri: str,
        symbol: str,
        process: Callable[[str, ExchangeResponseData], ExchangeResponseData],
    ) -> None:
        market: str = uri.split("//")[1].split(".")[1]
        p_message: dict = process
        await self.message_async_q.put((uri, market, p_message, symbol))

    async def message_producer(
        self, uri: str, market: str, message: ExchangeResponseData, symbol: str
    ) -> None:
        try:
            await self._logger.log_message(
                logging.INFO, message=f"{market} -- {message}"
            )
            self.message_by_data[market].append(message)
            if len(self.message_by_data[market]) >= 10:
                data = SocketLowData(
                    market=market,
                    uri=uri,
                    symbol=symbol,
                    data=self.message_by_data[market],
                )
                await KafkaMessageSender().produce_sending(
                    key=market,
                    message=data,
                    market_name=market,
                    symbol=symbol,
                    type_="SocketDataIn",
                )
                self.message_by_data[market].clear()
        except (TypeError, KeyError) as error:
            await self._logger.log_message(
                logging.ERROR,
                message=f"타입오류 --> {error} url --> {market}",
            )

    async def producing_start(self) -> None:
        uri, market, message, symbol = await self.message_async_q.get()
        await self.message_producer(
            uri=uri, market=market, message=message, symbol=symbol
        )


class WebsocketConnectionManager(WebsocketConnectionAbstract):
    """웹소켓 승인 전송 로직"""

    def __init__(
        self, target: str, folder: str, process: MessageDataPreprocessing
    ) -> None:
        self._logger = AsyncLogger(target=target, folder=folder)
        self.process = process

    async def socket_param_send(
        self, websocket: socket_protocol, subs_fmt: SubScribeFormat
    ) -> None:
        """socket 통신 요청 파라미터 보내는 메서드
        Args:
            websocket: 소켓 연결
            subs_fmt: 웹소켓 승인 스키마
        """
        sub = json.dumps(subs_fmt)
        await websocket.send(sub)

    async def handle_connection(self, websocket: socket_protocol, uri: str) -> None:
        """웹 소켓 커넥션 확인 함수
        Args:
            websocket: 소켓 연결
            uri: 각 uri들
        """
        message: str = await asyncio.wait_for(websocket.recv(), timeout=30.0)
        data = json.loads(message)
        market: str = uri.split("//")[1].split(".")[1]
        if data:
            await self._logger.log_message(logging.INFO, f"{market} 연결 완료")

    async def handle_message(
        self, websocket: socket_protocol, uri: str, symbol: str
    ) -> None:
        """메시지 전송하는 메서드"""
        while True:
            try:
                market: str = uri.split("//")[1].split(".")[1]
                message: ExchangeResponseData = await asyncio.wait_for(
                    websocket.recv(), timeout=30.0
                )
                await self.process.put_message_to_logging(
                    message=message, uri=uri, symbol=symbol, market=market
                )
                await self.process.producing_start()
            except (TypeError, ValueError) as error:
                message = f"다음과 같은 이유로 실행하지 못했습니다 --> {error}"
                self._logger.log_message(logging.ERROR, message)


class CommonCoinPresentPriceWebsocket:
    """Coin Stream"""

    def __init__(
        self,
        location: str,
        symbol: str,
        market: str = "all",
        market_type: str = "socket",
    ) -> None:
        """socket 시작
        Args:
            symbol: 긁어올 코인
            market: 활성화할 마켓. Defaults to "all"이면 모든 거래소 선택.
            market_type: Defaults to "socket".
        """
        tracemalloc.start()
        self.market = market
        self.symbol = symbol
        self.market_env = SocketMarketLoader(location).process_market_info()

    async def select_websocket(self) -> list:
        """마켓 선택"""
        parameter = self.market_env
        match self.market:
            case "all":
                return [
                    parameter[i]["api"].get_present_websocket(self.symbol)
                    for i in parameter
                ]
            case _:
                return [
                    parameter[self.market]["api"].get_present_websocket(self.symbol)
                ]

    async def coin_present_architecture(self) -> None:
        coroutines: list = await self.select_websocket()
        tasks = [asyncio.create_task(coro) for coro in coroutines]
        await asyncio.gather(*tasks, return_exceptions=False)
