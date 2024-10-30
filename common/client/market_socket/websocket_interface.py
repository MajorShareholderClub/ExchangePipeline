import json
import logging
import traceback
from typing import Callable
from collections import defaultdict
from asyncio.exceptions import CancelledError

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
                region=self.location,
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
        counting: int = metadata["counting"]
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
        self, message: str, kafka_metadata: ProducerMetadataDict
    ) -> None:
        """message에 따라 처리하고 적절한 함수를 호출"""

        def process_exchange(message: str | dict) -> dict | None:
            """message 필터링
            Args:
                message: 데이터 (JSON 문자열)
            Returns:
                dict | None: connection 거친 후 본 데이터, 필터링된 경우 None
            """
            try:
                if isinstance(message, str):
                    parsed_message = json.loads(message)
                else:
                    parsed_message = message  # 이미 dict인 경우

                match parsed_message:
                    case {"event": "korbit:subscribe"}:
                        return None  # 구독 메시지 무시
                    case {"response_type": "SUBSCRIBED"}:
                        return None  # 구독 메시지 무시
                    case {"channel": "heartbeat"}:
                        return None  # 구독 메시지 무시
                    case {"method": "subscribe"}:
                        return None  # 구독 메시지 무시
                    case _:
                        return message  # 본 데이터 반환

            except json.JSONDecodeError:
                return None  # JSON 파싱 오류가 발생하면 None 반환

        async def update_and_send(default_data: defaultdict, msg: dict) -> None:
            """메시지와 담을 default_data 선택하여 보내기"""
            kafka_metadata["default_data"] = default_data
            kafka_metadata["message"] = msg
            kafka_metadata["counting"] = 100

            await self.producer_sending(**kafka_metadata)

        # 메시지 필터링
        filtered_message = process_exchange(message)
        if filtered_message is None:
            await self._logger.log_message(
                logging.INFO, f"구독 메시지 무시됨: {message}"
            )
            return  # 구독 메시지를 무시하고 반환

        # 필터링된 메시지 처리
        match filtered_message:
            case {"type": "snapshot"}:
                await update_and_send(self.snapshot, filtered_message)
            case {"type": "update"}:
                await update_and_send(self.message_data, filtered_message)
            case _:
                await update_and_send(self.message_data, filtered_message)

    async def send_error_to_kafka(
        self, market: str, symbol: str, error: Exception
    ) -> None:
        """오류 메시지를 Kafka로 전송하는 메서드"""
        await self.send_kafka_message(
            market=market,
            symbol=symbol,
            data=[{"error": str(error)}],
            topic=f"{get_topic_name(self.location)}-error",
            key=f"{market}:error-{symbol}",
        )

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
                topic=f"{get_topic_name(self.location)}-{socket_type}",
                key=f"{market}:{socket_type}-{symbol}",
            )
            await self.append_and_process(
                message=message, kafka_metadata=producer_metadata
            )
        except (TypeError, KeyError, CancelledError) as error:
            message = f"오류 --> {error} market --> {market} symbol --> {symbol}"
            await self._logger.log_message(
                logging.ERROR,
                message=message,
            )
            await self.send_error_to_kafka(market, symbol, error)


class WebsocketConnectionManager(WebsocketConnectionAbstract):
    """웹소켓 승인 전송 로직"""

    def __init__(
        self,
        target: str,
        folder: str,
        process: Callable,
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

    async def handle_message(
        self,
        websocket: socket_protocol,
        uri: str,
        symbol: str = None,
        socket_type: str = None,
    ) -> None:
        """웹 소켓 커넥션 및 메시지 전송 처리"""
        market: str = market_name_extract(uri=uri)

        # 커넥션 초기 메시지 수신
        initial_message: str = await self.receive_message(websocket)
        if initial_message:
            await self._logger.log_message(logging.INFO, f"{market} 연결 완료")

        while True:
            try:
                # 메시지 수신
                message = await self.receive_message(websocket)
                if message:
                    await self.process.put_message_to_logging(
                        message=message, uri=uri, symbol=symbol
                    )
                    if socket_type:
                        await self.process.producing_start(socket_type=socket_type)
            except (TypeError, ValueError) as error:
                await self._logger.log_message(
                    logging.ERROR,
                    f"다음과 같은 이유로 실행하지 못했습니다 --> {error} \n 오류 라인 --> {traceback.format_exc()}",
                )
                await self.process.send_error_to_kafka(market, symbol, error)

    async def receive_message(self, websocket: socket_protocol) -> ExchangeResponseData:
        """메시지를 수신하고 JSON으로 변환하는 메서드"""
        try:
            message: bytes = await asyncio.wait_for(websocket.recv(), timeout=30.0)
            return json.loads(message) if isinstance(message, bytes) else message
        except (TypeError, ValueError) as error:
            message = f"다음과 같은 이유로 메시지 수신하지 못했습니다 --> {error} \n 오류 라인 --> {traceback.format_exc()}"
            await self._logger.log_message(logging.ERROR, message)
            await self.process.send_error_to_kafka("unknown", "unknown", error)

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
                await self.handle_message(websocket, uri, symbol, socket_type)

        await connection()
