import json
import logging
from typing import Callable
from collections import defaultdict

import websockets
import asyncio

from mq.data_interaction import KafkaMessageSender
from common.core.types import (
    SubScribeFormat,
    ExchangeResponseData,
    SocketLowData,
)
from common.exception import SocketRetryOnFailure
from common.utils.logger import AsyncLogger
from common.core.abstract import WebsocketConnectionAbstract
from common.setting.properties import (
    KOREA_REAL_TOPIC_NAME,
    FOREIGN_REAL_TOPIC_NAME,
)

socket_protocol = websockets.WebSocketClientProtocol


def market_name_extract(uri: str) -> str:
    """소켓 에서 마켓 이름 추출하는 메서드"""
    # 'wss://' 제거
    uri_parts = uri.split("//")[-1].split(".")

    # 도메인의 마지막 부분이 'coinbase'이면 그 부분을 선택
    if uri_parts[-2] == "coinbase":
        return uri_parts[-2].upper()

    # 그렇지 않으면 첫 번째 파트를 반환
    return uri_parts[1].upper()


# socket
class BaseMessageDataPreprocessing:
    def __init__(self, type_: str, location: str) -> None:
        self._logger = AsyncLogger(
            target=f"{type_}_websocket", folder=f"websocket_{location}"
        )
        self.location = location
        self.message_by_data = defaultdict(list)
        self.message_async_q = asyncio.Queue()

    async def put_message_to_logging(
        self,
        uri: str,
        symbol: str,
        process: Callable[[str, ExchangeResponseData], ExchangeResponseData],
    ) -> None:
        market: str = market_name_extract(uri=uri)
        p_message: dict = process
        await self.message_async_q.put((uri, market, p_message, symbol))

    async def message_producer(
        self,
        uri: str,
        market: str,
        message: ExchangeResponseData,
        symbol: str,
        socket_type: str,
    ) -> None:
        try:
            await self._logger.log_message(
                logging.INFO, message=f"{market} -- {message}"
            )
            self.message_by_data[market].append(message)

            if self.location.lower() == "korea":
                topic = f"{KOREA_REAL_TOPIC_NAME}{symbol.upper()}"
            else:
                topic = f"{FOREIGN_REAL_TOPIC_NAME}{symbol.upper()}"

            key: str = f"{market}:{socket_type}"
            if len(self.message_by_data[market]) >= 100:
                await KafkaMessageSender().produce_sending(
                    message=SocketLowData(
                        market=market,
                        uri=uri,
                        symbol=symbol,
                        data=self.message_by_data[market],
                    ),
                    topic=topic,
                    key=key,
                )
                self.message_by_data[market].clear()
        except (TypeError, KeyError) as error:
            await self._logger.log_message(
                logging.ERROR,
                message=f"타입오류 --> {error} url --> {market}",
            )

    async def producing_start(self, socket_type: str) -> None:
        uri, market, message, symbol = await self.message_async_q.get()
        await self.message_producer(
            uri=uri,
            market=market,
            message=message,
            symbol=symbol,
            socket_type=socket_type,
        )


class WebsocketConnectionManager(WebsocketConnectionAbstract):
    """웹소켓 승인 전송 로직"""

    def __init__(
        self,
        target: str,
        folder: str,
        process: BaseMessageDataPreprocessing,
        rest_client: SocketRetryOnFailure,
    ) -> None:
        self._logger = AsyncLogger(target=target, folder=folder)
        self.process = process
        self.rest_client = rest_client

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
        market: str = market_name_extract(uri=uri)
        if data:
            await self._logger.log_message(logging.INFO, f"{market} 연결 완료")

    async def handle_message(
        self, websocket: socket_protocol, uri: str, symbol: str, socket_type: str
    ) -> None:
        """메시지 전송하는 메서드"""
        while True:
            try:
                market: str = market_name_extract(uri=uri)
                message: ExchangeResponseData = await asyncio.wait_for(
                    websocket.recv(), timeout=30.0
                )
                await self.process.put_message_to_logging(
                    message=message, uri=uri, symbol=symbol, market=market
                )
                await self.process.producing_start(socket_type=socket_type)
            except (TypeError, ValueError) as error:
                message = f"다음과 같은 이유로 실행하지 못했습니다 --> {error}"
                self._logger.log_message(logging.ERROR, message)

    async def websocket_to_json(
        self,
        uri: str,
        subs_fmt: SubScribeFormat,
        symbol: str,
        socket_type: str,
    ) -> None:
        """말단 소켓 시작 지점"""

        @SocketRetryOnFailure(
            retries=3,
            base_delay=2,
            rest_client=self.rest_client,
            symbol=symbol,
            uri=uri,
            subs=subs_fmt,
        )
        async def connection():
            async with websockets.connect(
                uri, ping_interval=30.0, ping_timeout=60.0
            ) as websocket:
                await self.socket_param_send(websocket, subs_fmt)
                await self.handle_connection(websocket, uri)
                await self.handle_message(websocket, uri, symbol, socket_type)

        await connection()
