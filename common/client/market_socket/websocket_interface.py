import json
import logging
import traceback
from typing import TypedDict, Required
from collections import defaultdict
from asyncio.exceptions import CancelledError

import websockets
import asyncio
from config.yml_param_load import ticker_json
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


class MessageQueueData(TypedDict):
    market: Required[str]
    symbol: Required[str]
    message: Required[dict]


class KafkaMessageData(TypedDict):
    market: Required[str]
    symbol: Required[str]
    topic: Required[str]
    key: Required[str]
    data: Required[list[ResponseData]]


# fmt: off
class MessageQueueManager:
    """메시지 큐를 관리하는 클래스"""
    
    def __init__(self) -> None:
        self.message_async_q = asyncio.Queue()
        self.garbage_data = []

    def process_exchange(self, message: str | dict) -> dict:
        """거래소 메시지 처리
        
        Args:
            message: 처리할 메시지
            
        Returns:
            dict | None: 처리된 메시지 또는 None
        """
        try:
            if isinstance(message, str):
                parsed_message = json.loads(message)
            else:
                parsed_message = message

            match parsed_message:
                case {"response_type": "SUBSCRIBED"}:
                    return {"processed": "skip"}
                case {"channel": "heartbeat"}:
                    return {"processed": "skip"}
                case {"method": "subscribe"}:
                    return {"processed": "skip"}
                case _:
                    return parsed_message

        except json.JSONDecodeError:
            return None


    def process_filtered_data(self, filtered_message: ResponseData, ticker_columns: list[str]) -> ResponseData:
        """메시지 데이터를 필터링하여 처리"""
        def _process_data(data: dict | list, ticker_columns: list[str]) -> dict:
            """딕셔너리나 리스트 데이터를 처리"""
            target_dict = data[0] if isinstance(data, list) else data
            return {col: target_dict[col] for col in target_dict.keys() if col in ticker_columns}
        
        message_data = {}
        for key, value in filtered_message.items():
            if key not in ["data", "result", "time_ms", "ts", "timestamp"]:
                if key in ticker_columns:
                    message_data[key] = filtered_message[key]
                continue
                
            match value:
                case int() | float() as v:
                    message_data[key] = v
                case dict() | list() as d:
                    message_data.update(_process_data(d, ticker_columns))
                    
        return message_data

    async def put_message(self, uri: str, symbol: str, message: ResponseData, socket_type: str = None) -> None:
        """메시지를 큐에 추가
        
        Args:
            uri: 웹소켓 URI
            symbol: 심볼
            message: 응답 데이터
            socket_type: 소켓 타입
        """
        market: str = market_name_extract(uri=uri)
        
        if socket_type == "ticker":
            filtered_message = self.process_exchange(message)
            ticker_columns: list[str] = ticker_json(location=market)
            message_data = self.process_filtered_data(filtered_message, ticker_columns)
        else:
            message_data = message

        await self.message_async_q.put(
            MessageQueueData(
                market=market, 
                symbol=symbol, 
                message=json.dumps(message_data)
            )
        )


    async def get_message(self) -> MessageQueueData:
        """큐에서 메시지를 가져옴
        
        Returns:
            MessageQueueData: 큐에서 가져온 메시지 데이터
        """
        return await self.message_async_q.get()


class KafkaService:
    """Kafka 메시지 전송을 처리하는 서비스 클래스"""

    def __init__(self, location: str) -> None:
        self.location = location

    async def send_message(self, kafka_message: KafkaMessageData) -> None:
        """Kafka로 메시지 전송"""
        await KafkaMessageSender().produce_sending(
            message=SocketLowData(
                region=self.location,
                market=kafka_message["market"],
                symbol=kafka_message["symbol"],
                data=kafka_message["data"],
            ),
            topic=kafka_message["topic"],
            key=kafka_message["key"],
        )

    async def send_error(self, error: Exception, market: str, symbol: str) -> None:
        """에러 메시지를 Kafka로 전송
        
        Args:
            error: 발생한 예외
            market: 마켓 이름
            symbol: 심볼
        """
        await self.send_message(
            market=market,
            symbol=symbol,
            data=[{"error": str(error)}],
            topic="ErrorTopic",
            key=f"{market}:error-{symbol}",
        )


class MessageProcessor:
    """웹소켓 메시지 처리 클래스"""

    def __init__(self, logger: AsyncLogger, kafka_service: KafkaService) -> None:
        self._logger = logger
        self.kafka_service = kafka_service
        self.message_data = defaultdict(list)
        self.snapshot = defaultdict(list)



    async def update_and_send(self, default_data: defaultdict, msg: dict, kafka_metadata: ProducerMetadataDict) -> None:
        """메시지 업데이트 및 전송
        
        Args:
            default_data: 기본 데이터 저장소
            msg: 메시지
            kafka_metadata: Kafka 메타데이터
        """
        kafka_metadata["default_data"] = default_data
        kafka_metadata["message"] = msg
        kafka_metadata["counting"] = 100

        await self.producer_sending(**kafka_metadata)

    async def producer_sending(self, **metadata: ProducerMetadataDict) -> None:
        """메시지를 Kafka로 전송
        
        Args:
            metadata: Kafka 메타데이터 (market, symbol, topic, key, message, default_data, counting 포함)
        """
        default_data: defaultdict = metadata["default_data"]
        market: str = metadata["market"]
        counting: int = metadata["counting"]
        symbol: str = metadata["symbol"]
        message: ResponseData = metadata["message"]
        topic: str = metadata["topic"]
        key: str = metadata["key"]

        default_data[market].append(message)
        if len(default_data[market]) == counting:
            await self.kafka_service.send_message(
                kafka_message=KafkaMessageData(
                    market=market,
                    symbol=symbol,
                    data=default_data[market],
                    topic=topic,
                    key=key,
                )
            )
            default_data[market].clear()

    async def append_and_process(self, message: str, kafka_metadata: ProducerMetadataDict) -> None:
        """메시지 처리 및 추가
        
        Args:
            message: 처리할 메시지
            kafka_metadata: Kafka 메타데이터
        """

        match message:
            case {"type": "snapshot"}:
                await self.update_and_send(self.snapshot, message, kafka_metadata)
            case {"type": "update"}:
                await self.update_and_send(self.message_data, message, kafka_metadata)
            case _:
                await self.update_and_send(self.message_data, message, kafka_metadata)


class WebsocketConnectionManager(WebsocketConnectionAbstract):
    """웹소켓 연결 관리 클래스"""

    def __init__(self, location: str, folder: str, rest_client: SocketRetryOnFailure) -> None:
        self._logger = AsyncLogger(target=location, folder=folder)
        self.rest_client = rest_client
        self.message_queue = MessageQueueManager()
        self.kafka_service = KafkaService(location=location)
        self.message_processor = MessageProcessor(logger=self._logger, kafka_service=self.kafka_service)

    async def handle_message(self, websocket: socket_protocol, uri: str, symbol: str = None, socket_type: str = None) -> None:
        """웹소켓 메시지 처리
        
        Args:
            websocket: 웹소켓 프로토콜
            uri: 웹소켓 URI
            symbol: 심볼
            socket_type: 소켓 타입
        """
        market: str = market_name_extract(uri=uri)

        initial_message: str = await self.receive_message(websocket)
        if initial_message:
            await self._logger.log_message(logging.INFO, f"{market} 연결 완료")

        while True:
            try:
                message = await self.receive_message(websocket)
                await self.message_queue.put_message(uri=uri, symbol=symbol, message=message, socket_type=socket_type)
                await self.producing_start(socket_type)
            except (TypeError, ValueError, Exception) as error:
                await self._logger.log_message(
                    logging.ERROR,
                    f"다음과 같은 이유로 실행하지 못했습니다 --> {error} \n 오류 라인 --> {traceback.format_exc()}",
                )
                await self.kafka_service.send_error(error, market, symbol)

    async def receive_message(self, websocket: socket_protocol) -> ExchangeResponseData:
        """웹소켓에서 메시지 수신
        Args:
            websocket: 웹소켓 프로토콜
            
        Returns:
            ExchangeResponseData: 수신된 메시지
        """
        try:
            # message: bytes = await asyncio.wait_for(websocket.recv(), timeout=30.0)
            message: bytes = await websocket.recv()
            return json.loads(message) if isinstance(message, bytes | str) else message
        except (TypeError, ValueError) as error:
            message = f"다음과 같은 이유 메시지 수신하지 못했습니다 --> {error} \n 오류 라인 --> {traceback.format_exc()}"
            await self._logger.log_message(logging.ERROR, message)
            await self.kafka_service.send_error(error, "Socket", "Socket")

    async def producing_start(self, socket_type: str) -> None:
        """메시지 생성 및 처리 시작
        
        Args:
            socket_type: 소켓 타입
        """
        try:
            queue_data: MessageQueueData = await self.message_queue.get_message()
            market: str = queue_data["market"]
            symbol: str = queue_data["symbol"]
            message: ResponseData = json.loads(queue_data["message"])
            
            if len(message) > 0:
                await self._logger.log_message(logging.INFO, message=f"{market} -- {message}")
                producer_metadata = ProducerMetadataDict(
                    market=market,
                    symbol=symbol,
                    topic=f"{get_topic_name(location=self.kafka_service.location)}-{socket_type}",
                    key=f"{market}:{socket_type}-{symbol}",
                ) 
            
                await self.message_processor.append_and_process(message=json.dumps(message), kafka_metadata=producer_metadata)
        except (TypeError, KeyError, CancelledError) as error:
            message = f"오류 --> {error} market --> {market} symbol --> {symbol}"
            await self._logger.log_message(logging.ERROR, message=message)
            await self.kafka_service.send_error(error, market, symbol)

    async def websocket_to_json(self, uri: str, subs_fmt: SubScribeFormat, symbol: str, socket_type: str) -> None:
        """웹소켓 연결 및 JSON 변환 처리
        
        Args:
            uri: 웹소켓 URI
            subs_fmt: 구독 형식
            symbol: 심볼
            socket_type: 소켓 타입
        """
        @SocketRetryOnFailure(
            retries=3,
            base_delay=2,
            rest_client=self.rest_client,
            symbol=symbol,
            uri=uri,
            subs=subs_fmt,
        )
        async def connection():
            async with websockets.connect(uri, ping_interval=30.0, ping_timeout=60.0) as websocket:
                await websocket.send(json.dumps(subs_fmt))
                await self.handle_message(websocket, uri, symbol, socket_type)

        await connection()
