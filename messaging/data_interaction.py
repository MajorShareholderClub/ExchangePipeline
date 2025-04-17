import json
import asyncio
from pathlib import Path
from typing import Any, TypedDict, Callable
from datetime import datetime
from dataclasses import dataclass

from decimal import Decimal
from aiokafka import AIOKafkaProducer
from common.exceptions import KafkaException
from messaging.data_partitional import CompositeKeyHashPartitioner

from common.logger import PipelineLogger
from common.setting.properties import (
    BOOTSTRAP_SERVER,
    SECURITY_PROTOCOL,
    MAX_BATCH_SIZE,
    MAX_REQUEST_SIZE,
    ACKS,
)

present_path = Path(__file__).parent
Serializer = Callable[[Any], bytes]

# decimal string converting
dsc: Serializer = lambda obj: str(obj) if isinstance(obj, Decimal) else obj
serializer: bytes = lambda value: json.dumps(value, default=dsc).encode("utf-8")


class KafkaConfig(TypedDict):
    bootstrap_servers: str = BOOTSTRAP_SERVER
    security_protocol: str = SECURITY_PROTOCOL
    max_batch_size: int = MAX_BATCH_SIZE
    max_request_size: int = MAX_REQUEST_SIZE
    partitioner: CompositeKeyHashPartitioner
    acks: str | int
    value_serializer: bytes
    key_serializer: bytes
    enable_idempotence: bool
    retry_backoff_ms: int


@dataclass
class KafkaMessageSender:
    """
    KafkaMessageSender
    - 카프카 전송 로직
    """

    producer: AIOKafkaProducer | None = None
    producer_started: bool = False
    partition_pol: CompositeKeyHashPartitioner = CompositeKeyHashPartitioner()
    logger: PipelineLogger = PipelineLogger.get_logger("kafka", "sender")

    # 실행할 비동기 함수, 예: self.producer.start 또는 self.producer.stop
    async def _execute_with_logging(
        self, action: Callable, success: str, failure: str
    ) -> bool:
        """지정된 action을 실행하며 로깅을 처리하는 헬퍼 비동기 메서드"""
        try:
            await action()
            await self.logger.ainfo(msg=f"{datetime.now()} - {success}")
            return True
        except KafkaException as e:
            await self.logger.ainfo(msg=f"{datetime.now()} - {failure}: {e}")
            return False

    # fmt: off
    async def start_producer(self) -> None:
        """Producer 시작 및 재사용"""
        if not self.producer_started:
            config = KafkaConfig(
                bootstrap_servers=BOOTSTRAP_SERVER,
                security_protocol=SECURITY_PROTOCOL,
                max_batch_size=int(MAX_BATCH_SIZE),
                max_request_size=int(MAX_REQUEST_SIZE),
                partitioner=self.partition_pol,
                acks=ACKS,
                value_serializer=serializer,
                key_serializer=serializer,
                enable_idempotence=True,
                retry_backoff_ms=100,
            )
            self.producer = AIOKafkaProducer(**config)
        # 헬퍼 메서드를 통해 시작 시도
        result = await self._execute_with_logging(
            action=self.producer.start,
            success="Kafka Producer 시작 성공",
            failure="Producer 시작 실패",
        )
        if result:
            self.producer_started = True

    async def stop_producer(self) -> None:
        """Producer 종료"""
        if self.producer_started and self.producer is not None:
            result = await self._execute_with_logging(
                action=self.producer.stop,
                success="Kafka Producer 종료 성공",
                failure="Producer 종료 실패",
            )
            if result:
                self.producer_started = False

    async def produce_sending(
        self, message: dict, topic: str, key: bytes, retries: int = 3
    ) -> None:
        await self.start_producer()
        attempt = 1
        while attempt <= retries:
            try:
                size: int = len(json.dumps(message, default=dsc).encode("utf-8"))
                log_message: str = f"{datetime.now()}-Message to: {topic} --> size: {size} bytes, attempt {attempt}"
                await self.logger.ainfo(msg=log_message)
                await self.producer.send_and_wait(topic=topic, value=message, key=key)
                await self.logger.ainfo(msg=f"{datetime.now()}-Message 전송 성공 on attempt {attempt}")
            except KafkaException as e:
                await self.logger.ainfo(msg=f"{datetime.now()}-Message 전송 실패 on attempt {attempt}: {e}")
                attempt += 1
                await asyncio.sleep(attempt)
        raise KafkaException(f"{datetime.now()}-메시지를 {retries}회 시도 후에도 전송하지 못했습니다.")
