import logging
import tracemalloc
import asyncio
from collections import defaultdict

import json
import websockets
from pipe.foreign.foreign_rest_client import ForeignExchangeRestAPI
from common.core.abstract import (
    MessageDataPreprocessingAbstract,
    WebsocketConnectionAbstract,
)
from common.exception import SocketRetryOnFailure
from common.exception import AsyncLogger
from common.core.types import SubScribeFormat, ExchangeResponseData, SocketLowData
from config.json_param_load import load_json
from mq.data_interaction import KafkaMessageSender

socket_protocol = websockets.WebSocketClientProtocol
MAXLISTSIZE = 10


class WebsocketConnectionManager(WebsocketConnectionAbstract):
    """웹소켓 승인 전송 로직"""

    def __init__(self) -> None:
        self.message_preprocessing = MessageDataPreprocessing()
        self._logger = AsyncLogger(target="websocket", folder="websocket")

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
            message: ExchangeResponseData = await asyncio.wait_for(
                websocket.recv(), timeout=30.0
            )
            market: str = uri.split("//")[1].split(".")[1]

            await self.message_preprocessing.add_to_queue(
                message=message, uri=uri, symbol=symbol, market=market
            )
            await self.message_preprocessing.message_producer()
            # await asyncio.sleep(1.0)

    async def websocket_to_json(
        self, uri: str, subs_fmt: SubScribeFormat, symbol: str
    ) -> None:
        """말단 소켓 시작 지점"""

        @SocketRetryOnFailure(
            retries=3,
            base_delay=2,
            rest_client=ForeignExchangeRestAPI(),
            symbol=symbol,
            uri=uri,
            subs=subs_fmt,
        )
        async def connection() -> None:
            async with websockets.connect(
                uri, ping_interval=30.0, ping_timeout=60.0
            ) as websocket:
                await self.socket_param_send(websocket, subs_fmt)
                await self.handle_connection(websocket, uri)
                await self.handle_message(websocket, uri, symbol)

        await connection()


class MessageDataPreprocessing(MessageDataPreprocessingAbstract):
    def __init__(self) -> None:
        self.market = load_json("socket", "foreign")
        self._logger = AsyncLogger(target="websocket", folder="websocket_foregin")
        self.message_by_data = defaultdict(list)
        self.async_q = asyncio.Queue()

    # fmt: off
    async def add_to_queue(self, message: ExchangeResponseData, uri: str, symbol: str, market: str) -> None:
        """메시지를 큐에 추가"""
        await self.async_q.put((json.loads(message), uri, symbol, market))

    async def message_producer(self) -> None:
        """메시지 소비"""
        
        message, uri, symbol, market = await self.async_q.get()
        if isinstance(message, dict):
            if "arg" in list(message.keys()):
                del message["arg"]
                message = message["data"]
            else:
                message = message
                
        try:                  
            await self._logger.log_message(
                logging.INFO, message=f"{market} -- {message}"
            )
            self.message_by_data[market].append(message)
            if len(self.message_by_data[market]) >= 100:
                data = SocketLowData(
                    market=market,
                    uri=uri,
                    symbol=symbol,
                    data=self.message_by_data[market]
                )
                await KafkaMessageSender().produce_sending(
                    key=market,
                    message=data,
                    market_name=market,
                    symbol=symbol,
                    type_="SocketDataIn",
                )
                self.async_q.task_done()            
                self.message_by_data[market].clear()

        except (TypeError, KeyError) as error:
            await self._logger.log_message(
                logging.ERROR,
                message=f"타입오류 --> {error} url --> {market}",
            )


class ForeignCoinPresentPriceWebsocket:
    """Coin Stream"""

    def __init__(
        self, symbol: str, market: str = "all", market_type: str = "socket"
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
        self.market_env = load_json(market_type, "foreign")

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
        """실행 지점"""
        coroutines: list = await self.select_websocket()
        await asyncio.gather(*coroutines, return_exceptions=False)
