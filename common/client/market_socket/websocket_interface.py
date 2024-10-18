import json
import logging
from typing import Callable
from collections import defaultdict

import websockets
import asyncio

from mq.data_interaction import KafkaMessageSender
from common.exception import SocketRetryOnFailure
from common.utils.logger import AsyncLogger
from common.utils.other_util import market_name_extract, get_topic_name
from common.core.abstract import WebsocketConnectionAbstract
from common.core.types import (
    SubScribeFormat,
    ExchangeResponseData,
    ResponseData,
    SocketLowData,
    ProducerMetadataDict,
)

socket_protocol = websockets.WebSocketClientProtocol


# socket
class BaseMessageDataPreprocessing:
    def __init__(self, type_: str, location: str) -> None:
        """메시지 처리할 원초 클래스

        Args:
            type_ (str): response type
            location (str): 지역(한국, 해외)
        """
        self._logger = AsyncLogger(
            target=f"{type_}_websocket", folder=f"websocket_{location}"
        )
        self.location = location
        self.message_data = defaultdict(list)
        self.snapshot = defaultdict(list)
        self.heartbeat = defaultdict(list)
        self.message_async_q = asyncio.Queue()

    async def put_message_to_logging(
        self, market: str, symbol: str, message: ResponseData
    ) -> None:
        """메시지 가 들어오면 비동기 큐에 넣는 함수"""
        await self.message_async_q.put((market, message, symbol))

    async def send_kafka_message(
        self, market: str, symbol: str, data: list, topic: str, key: str
    ) -> None:
        """Kafka에 메시지 전송"""
        await KafkaMessageSender().produce_sending(
            message=SocketLowData(
                market=market,
                symbol=symbol,
                data=data,
            ),
            topic=topic,
            key=key,
        )

    async def producer_sending(self, **metadata: ProducerMetadataDict) -> None:
        """Kafka로 메시지를 전송하고, 데이터가 count 만큼 다 차면 clear"""
        default_data: defaultdict = metadata["default_data"]
        market: str = metadata["market"]
        counting: int = metadata["couting"]
        symbol: str = metadata["symbol"]
        message: ResponseData = metadata["message"]
        topic: str = metadata["topic"]
        key: str = metadata["key"]

        default_data[market].append(message)
        if len(default_data[market]) == counting:
            cleared_data = default_data[market].copy()  # 데이터 복사
            await self.send_kafka_message(market, symbol, cleared_data, topic, key)
            default_data[market].clear()  # 데이터를 비우기

    async def append_and_process(
        self, message: ResponseData, kafka_metadata: ProducerMetadataDict
    ) -> None:
        """message에 따라 처리하고 적절한 함수를 호출"""

        async def update_and_send(default_data: defaultdict, msg: ResponseData) -> None:
            """메시지와 담을 default_data 선택하여 보내기"""
            kafka_metadata["default_data"] = default_data
            kafka_metadata["message"] = msg
            kafka_metadata["couting"] = 100

            await self.producer_sending(**kafka_metadata)

        # 크라켄 메시지 처리
        match message:
            case {"channel": "heartbeat"}:
                await update_and_send(self.heartbeat, message)
            case {"type": "snapshot"}:
                await update_and_send(self.snapshot, message)
            case {"type": "update"}:
                await update_and_send(self.message_data, message)
            case _:
                await update_and_send(self.message_data, message)

    async def producing_start(self, socket_type: str) -> None:
        """프로듀싱 시작점 socket_type: (orderbook, ticker)"""
        try:
            market, message, symbol = await self.message_async_q.get()
            await self._logger.log_message(
                logging.INFO, message=f"{market} -- {message}"
            )

            producer_metadata = ProducerMetadataDict(
                market=market,
                symbol=symbol,
                topic=get_topic_name(self.location, symbol),
                key=f"{market}:{socket_type}",
            )
            await self.append_and_process(
                message=message, kafka_metadata=producer_metadata
            )
        except (TypeError, KeyError, Exception) as error:
            await self._logger.log_message(
                logging.ERROR,
                message=f"타입오류 --> {error} market --> {market}",
            )


class WebsocketConnectionManager(WebsocketConnectionAbstract):
    """웹소켓 승인 전송 로직"""

    def __init__(
        self,
        target: str,
        folder: str,
        process: Callable,
        # rest_client: SocketRetryOnFailure,
    ) -> None:
        self._logger = AsyncLogger(target=target, folder=folder)
        self.process = process
        # self.rest_client = rest_client

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
                message: ExchangeResponseData = await asyncio.wait_for(
                    websocket.recv(), timeout=30.0
                )
                await self.process.put_message_to_logging(
                    message=message, uri=uri, symbol=symbol
                )
                await self.process.producing_start(socket_type=socket_type)
            except (TypeError, ValueError) as error:
                message = f"다음과 같은 이유로 실행하지 못했습니다 --> {error}"
                await self._logger.log_message(logging.ERROR, message)
                import traceback

                traceback.print_exc()  # 스택 트레이스를 출력

    async def websocket_to_json(
        self,
        uri: str,
        subs_fmt: SubScribeFormat,
        symbol: str,
        socket_type: str,
    ) -> None:
        """말단 소켓 시작 지점"""

        # @SocketRetryOnFailure(
        #     retries=3,
        #     base_delay=2,
        #     rest_client=self.rest_client,
        #     symbol=symbol,
        #     uri=uri,
        #     subs=subs_fmt,
        # )
        async def connection():
            async with websockets.connect(
                uri, ping_interval=30.0, ping_timeout=60.0
            ) as websocket:
                await self.socket_param_send(websocket, subs_fmt)
                await self.handle_connection(websocket, uri)
                await self.handle_message(websocket, uri, symbol, socket_type)

        await connection()
