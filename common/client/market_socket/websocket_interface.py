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

    def process_exchange(self, message: str | dict) -> dict | None:
        """거래소 메시지를 처리하는 메서드
        
        Args:
            message: 처리할 메시지 (문자열 또는 딕셔너리)
            
        Returns:
            dict | None: 처리된 메시지 또는 None (오류 발생 시)
        """
        # 무시할 메시지 패턴 정의
        SKIP_PATTERNS = [
            {"response_type": "SUBSCRIBED"},  # 구독 확인 메시지
            {"channel": "heartbeat"},        # 하트비트 메시지
            {"method": "subscribe"},       # 구독 요청 메시지
        ]
        
        try:
            # 문자열이면 JSON으로 파싱
            parsed_message = json.loads(message) if isinstance(message, str) else message
            
            # 무시할 패턴에 대한 검사
            for pattern in SKIP_PATTERNS:
                # 패턴의 모든 키-값 쌍이 메시지에 있는지 확인
                if all(parsed_message.get(k) == v for k, v in pattern.items()):
                    return {"processed": "skip"}
            
            # 패턴에 맞지 않는 메시지는 그대로 반환
            return parsed_message
            
        except json.JSONDecodeError:
            # JSON 파싱 오류 발생 시 None 반환
            return None


    def process_filtered_data(self, filtered_message: ResponseData, ticker_columns: list[str]) -> ResponseData:
        """메시지 데이터를 필터링하여 처리하는 메서드
        
        Args:
            filtered_message: 필터링할 응답 데이터
            ticker_columns: 필터링에 사용할 컬럼 목록
            
        Returns:
            ResponseData: 필터링된 메시지 데이터
        """
        # 특수 키 목록 정의
        special_keys = {"data", "result", "time_ms", "ts", "timestamp"}
        
        # 기본 메시지 데이터 생성 - 필터링된 일반 필드
        message_data = {k: v for k, v in filtered_message.items() 
                        if k not in special_keys and k in ticker_columns}
        
        # 특수 키 처리
        for key in special_keys & filtered_message.keys():  # 교집합으로 존재하는 키만 처리
            value = filtered_message[key]
            
            # 숫자 타입은 그대로 추가
            if isinstance(value, (int, float)):
                message_data[key] = value
            # 딕셔너리나 리스트는 필터링하여 추가
            elif isinstance(value, (dict, list)):
                target_dict = value[0] if isinstance(value, list) else value
                # 딕셔너리 컴프리헨션으로 필터링
                message_data.update({col: target_dict[col] for col in set(target_dict) & set(ticker_columns)})
                
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
            message_data = filtered_message = self.process_exchange(message)
            


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
        self.last_send_time = defaultdict(float)
        self.BATCH_SIZE = 100  # 배치 크기
        self.TIME_THRESHOLD = 60.0  # 시간 임계값 (초)

    async def should_send_batch(self, market: str, data_size: int) -> bool:
        """배치를 전송해야 하는지 확인
        
        Args:
            market: 마켓 이름
            data_size: 현재 데이터 크기
            
        Returns:
            bool: 전송 여부
        """
        current_time = asyncio.get_event_loop().time()
        time_elapsed = current_time - self.last_send_time[market]
        
        return (data_size >= self.BATCH_SIZE) or (time_elapsed >= self.TIME_THRESHOLD)

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
        """메시지를 Kafka로 전송"""
        default_data: defaultdict = metadata["default_data"]
        market: str = metadata["market"]
        symbol: str = metadata["symbol"]
        message: ResponseData = metadata["message"]
        topic: str = metadata["topic"]
        key: str = metadata["key"]

        default_data[market].append(message)
        current_size = len(default_data[market])

        # 배치 전송 조건 확인 (배치 크기 또는 시간 임계값)
        if await self.should_send_batch(market, current_size):
            if current_size > 0: 
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
                self.last_send_time[market] = asyncio.get_event_loop().time()

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
            message: bytes = await asyncio.wait_for(websocket.recv(), timeout=30.0)
            # message: bytes = await websocket.recv()
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
                if message.get("processed") == "skip":
                    return
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
