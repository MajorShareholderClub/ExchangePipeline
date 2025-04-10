import json
from pathlib import Path
from typing import Any, TypedDict, Callable

from decimal import Decimal
from aiokafka import AIOKafkaProducer
from common.exceptions import KafkaException
from kafka.partitioner.default import DefaultPartitioner
from messaging.data_partitional import (
    CoinHashingCustomPartitional,
    CoinSocketDataCustomPartition,
)
from common.logger import PipelineLogger
from common.setting.properties import (
    BOOTSTRAP_SERVER,
    SECURITY_PROTOCOL,
    MAX_BATCH_SIZE,
    MAX_REQUEST_SIZE,
    ACKS,
)

present_path = Path(__file__).parent


def default(obj: Any):
    if isinstance(obj, Decimal):
        return str(obj)


class KafkaConfig(TypedDict):
    bootstrap_servers: str
    security_protocol: str
    max_batch_size: int
    max_request_size: int
    partitioner: (
        DefaultPartitioner
        | CoinHashingCustomPartitional
        | CoinSocketDataCustomPartition
    )
    acks: str | int
    value_serializer: Callable[[Any], bytes]
    key_serializer: Callable[[Any], bytes]
    enable_idempotence: bool
    retry_backoff_ms: int


class KafkaMessageSender:
    """
    KafkaMessageSender
    - 카프카 전송 로직
    - 전송 실패 시 메시지를 임시 저장하고, 나중에 재전송
    """

    def __init__(
        self, partition_pol: Callable = CoinSocketDataCustomPartition()
    ) -> None:
        self.producer: AIOKafkaProducer | None = None  # Producer를 클래스 속성으로 저장
        self.producer_started = False
        self.partition_pol = partition_pol
        self.logger = PipelineLogger.get_logger("kafka", "sender")

    # fmt: off
    async def start_producer(self, topic: str, message: dict) -> None:
        """Producer 시작 및 재사용"""
        if not self.producer_started:
            config = KafkaConfig(
                bootstrap_servers=BOOTSTRAP_SERVER,
                security_protocol=SECURITY_PROTOCOL,
                max_batch_size=int(MAX_BATCH_SIZE),
                max_request_size=int(MAX_REQUEST_SIZE),
                partitioner=self.partition_pol,
                acks=ACKS,
                value_serializer=lambda value: json.dumps(value, default=default).encode("utf-8"),
                key_serializer=lambda value: json.dumps(value, default=default).encode("utf-8"),
                enable_idempotence=True,
                retry_backoff_ms=100,
            )
            self.producer = AIOKafkaProducer(**config)
            try:
                await self.producer.start()
                self.producer_started = True
            except KafkaException as e:
                await self.logger.ainfo(message=f"Producer 시작 실패: {e} ")
                
    async def stop_producer(self) -> None:
        """Producer 종료"""
        if self.producer_started and self.producer is not None:
            try:
                await self.producer.stop()
                self.producer_started = False
            except KafkaException as e:
                await self.logger.ainfo(message=f"Producer 종료 실패: {e}")


    async def produce_sending(self, message: dict, topic: str, key: bytes) -> None:
        await self.start_producer(topic, message)

        try:
            # 로그는 실제 전송할 메시지와는 별도로 기록
            size: int = len(json.dumps(message, default=default).encode("utf-8"))
            log_message = f"Message to: {topic} --> size: {size} bytes"
            await self.logger.ainfo(message=log_message)

            # 실제 메시지 전송
            await self.producer.send_and_wait(
                topic=topic, value=message, key=key
            )
        finally:
            await self.stop_producer()
