import json
import logging
import tracemalloc
from collections import defaultdict

import websockets
import asyncio

from typing import Callable
from config.yml_param_load import SocketMarketLoader

from mq.data_interaction import KafkaMessageSender
from common.core.types import (
    SubScribeFormat,
    SocketLowData,
    ExchangeResponseData,
)
from common.utils.logger import AsyncLogger
from common.core.abstract import (
    WebsocketConnectionAbstract,
)

socket_protocol = websockets.WebSocketClientProtocol

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
                # await KafkaMessageSender().produce_sending(
                #     key=market,
                #     message=data,
                #     market_name=market,
                #     symbol=symbol,
                #     type_="SocketDataIn",
                # )
                # self.message_by_data[market].clear()
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


class MarketsCoinTickerPriceWebsocket:
    """Coin Stream"""

    def __init__(
        self,
        location: str,
        symbol: str,
        market: str = "all",
    ) -> None:
        """socket 시작
        Args:
            symbol: 긁어올 코인
            market: 활성화할 마켓. Defaults to "all"이면 모든 거래소 선택.
            market_type: Defaults to "socket".
        """
        self.market = market
        self.symbol = symbol
        self.market_env = SocketMarketLoader(location).process_market_info()

    async def select_websocket(self) -> list:
        """마켓 선택"""
        parameter = self.market_env
        match self.market:
            case "all":
                return [
                    parameter[i]["api"].orderbook_present_websocket(self.symbol)
                    for i in parameter
                ]
            case _:
                return [
                    parameter[self.market]["api"].orderbook_present_websocket(
                        self.symbol
                    )
                ]

    async def coin_present_architecture(self) -> None:
        coroutines: list = await self.select_websocket()
        await asyncio.gather(*coroutines, return_exceptions=False)
