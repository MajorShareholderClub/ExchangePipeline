import asyncio
from typing import Any, Optional

from aiokafka import AIOKafkaProducer
from messaging.models.exchange_events import ExchangeEvent


class EventProducer:
    """이벤트 생산자
    
    이벤트를 메시지 브로커(Kafka)로 전송하는 클래스입니다.
    """
    
    def __init__(self, bootstrap_servers: str = "localhost:9092"):
        """초기화
        
        Args:
            bootstrap_servers: Kafka 서버 주소
        """
        self.bootstrap_servers = bootstrap_servers
        self.producer: Optional[AIOKafkaProducer] = None
    
    async def start(self) -> None:
        """생산자 시작
        
        Kafka 생산자를 초기화하고 시작합니다.
        """
        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda v: v.json().encode("utf-8"),  # Pydantic 모델을 JSON으로 직렬화
        )
        await self.producer.start()
    
    async def stop(self) -> None:
        """생산자 종료
        
        Kafka 생산자를 종료합니다.
        """
        if self.producer is not None:
            await self.producer.stop()
    
    async def send_event(self, topic: str, event: ExchangeEvent) -> None:
        """이벤트 전송
        
        이벤트를 지정된 토픽으로 전송합니다.
        
        Args:
            topic: Kafka 토픽 이름
            event: 전송할 이벤트 객체
        """
        if self.producer is None:
            raise RuntimeError("Producer is not started. Call start() first.")
        
        # 이벤트를 Kafka로 전송
        await self.producer.send_and_wait(topic, event)
    
    async def __aenter__(self) -> "EventProducer":
        """비동기 컨텍스트 관리자 진입"""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """비동기 컨텍스트 관리자 종료"""
        await self.stop()
