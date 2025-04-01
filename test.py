import asyncio
import json
import websockets
from typing import Any, Dict
import logging

# EDA 관련 임포트
from adapters.base.event.event_bus import EventBus
from adapters.base.event.types import EventType, EventMetadata, EventPriority
from common.setting.parameter.connection_parameter import (
    bithumb_config,
    upbit_config,
    binance_config,
    bybit_config,
    coinone_config
)

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('ticker_subscriber')


class TickerHandler:
    """거래소 티커 데이터 핸들러
    
    웹소켓 연결 및 이벤트 발행을 담당합니다.
    """
    
    def __init__(self, event_bus: EventBus, exchange_name: str):
        self.event_bus = event_bus
        self.exchange_name = exchange_name
        self.connected = False
    
    async def connect_and_subscribe(self, config: Dict[str, Any]) -> None:
        """웹소켓에 연결하고 티커 데이터를 구독합니다.
        
        Args:
            config: 연결 설정 정보
        """
        url: str = config["url"]
        socket_parameters: Dict | list = config["parameters"]
        timeout: int = config["timeout"]
        
        if not socket_parameters:
            logger.warning(f"{self.exchange_name}: 소켓 파라미터가 없습니다.")
            return
            
        try:
            # 연결 시작 이벤트 발행
            await self.event_bus.publish(
                EventType.EXCHANGE_CONNECT,
                {"exchange": self.exchange_name, "status": "connecting"},
                EventMetadata(priority=EventPriority.HIGH, source=self.exchange_name)
            )
            
            logger.info(f"{self.exchange_name}: 연결 시도 중... {url}")
            
            async with websockets.connect(
                url,
                ping_interval=30,
                ping_timeout=60,
            ) as websocket:
                # 연결 성공 처리
                self.connected = True
                logger.info(f"{self.exchange_name}: 연결 성공")
                
                # 연결 성공 이벤트 발행
                await self.event_bus.publish(
                    EventType.EXCHANGE_CONNECT,
                    {"exchange": self.exchange_name, "status": "connected"},
                    EventMetadata(priority=EventPriority.MEDIUM, source=self.exchange_name)
                )
                
                # 파라미터 전송
                param_json = json.dumps(socket_parameters)
                await websocket.send(param_json)
                logger.info(f"{self.exchange_name}: 구독 파라미터 전송 완료")
                
                # 메시지 수신 및 이벤트 발행
                while True:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=timeout)
                        await self._process_message(message)
                    except asyncio.TimeoutError:
                        logger.warning(f"{self.exchange_name}: 타임아웃 발생")
                        break
                        
        except Exception as e:
            logger.error(f"{self.exchange_name}: 연결 오류 - {str(e)}")
            # 오류 이벤트 발행
            await self.event_bus.publish(
                EventType.EXCHANGE_ERROR,
                {"exchange": self.exchange_name, "error": str(e)},
                EventMetadata(priority=EventPriority.HIGH, source=self.exchange_name)
            )
        finally:
            # 연결 종료 처리
            if self.connected:
                self.connected = False
                await self.event_bus.publish(
                    EventType.EXCHANGE_DISCONNECT,
                    {"exchange": self.exchange_name, "status": "disconnected"},
                    EventMetadata(priority=EventPriority.MEDIUM, source=self.exchange_name)
                )
    
    async def _process_message(self, message: Any) -> None:
        """수신된 메시지 처리 및 이벤트 발행
        
        Args:
            message: 수신된 웹소켓 메시지
        """
        try:
            # bytes 메시지 처리
            if isinstance(message, bytes):
                message = message.decode('utf-8')
                
            # JSON 문자열 처리
            if isinstance(message, str):
                try:
                    data = json.loads(message)
                    # Ticker 데이터 이벤트 발행
                    await self.event_bus.publish(
                        EventType.MARKET_TICKER,
                        {
                            "exchange": self.exchange_name,
                            "timestamp": asyncio.get_event_loop().time(),
                            "data": data
                        },
                        EventMetadata(source=self.exchange_name)
                    )
                except json.JSONDecodeError:
                    logger.warning(f"{self.exchange_name}: JSON 파싱 오류 - {message[:100]}...")
            else:
                logger.warning(f"{self.exchange_name}: 지원하지 않는 메시지 타입 - {type(message)}")
                
        except Exception as e:
            logger.error(f"{self.exchange_name}: 메시지 처리 오류 - {str(e)}")


# 이벤트 핸들러 함수 (콜백)
def handle_ticker(data: Dict[str, Any]) -> None:
    """티커 이벤트 처리 핸들러"""
    exchange = data.get("exchange", "unknown")
    timestamp = data.get("timestamp", "N/A")
    ticker_data = data.get("data", {})
    
    # 거래소별 다른 포맷의 데이터 처리
    # 간단하게 로그만 출력하지만, 실제로는 통합된 포맷으로 변환하거나 후속 처리 가능
    logger.info(f"[{exchange}] 티커 수신: {json.dumps(ticker_data)[:100]}...")


def handle_connection_event(data: Dict[str, Any]) -> None:
    """연결 이벤트 처리 핸들러"""
    exchange = data.get("exchange", "unknown")
    status = data.get("status", "unknown")
    logger.info(f"[{exchange}] 연결 상태 변경: {status}")


def handle_error(data: Dict[str, Any]) -> None:
    """오류 이벤트 처리 핸들러"""
    exchange = data.get("exchange", "unknown")
    error = data.get("error", "unknown")
    logger.error(f"[{exchange}] 오류 발생: {error}")


async def run_ticker_subscribers() -> None:
    """티커 구독 실행 함수"""
    # 이벤트 버스 초기화
    event_bus = EventBus()
    await event_bus.start()
    
    try:
        # 이벤트 핸들러 등록
        await event_bus.subscribe(EventType.MARKET_TICKER, handle_ticker)
        await event_bus.subscribe(EventType.EXCHANGE_CONNECT, handle_connection_event)
        await event_bus.subscribe(EventType.EXCHANGE_DISCONNECT, handle_connection_event)
        await event_bus.subscribe(EventType.EXCHANGE_ERROR, handle_error)
        
        # 초기 거래소 설정 (10개 중 일부)
        exchanges = [
            ("bithumb", bithumb_config.build()),
            ("upbit", upbit_config.build()),
            ("binance", binance_config.build()),
            ("bybit", bybit_config.build()),
            ("coinone", coinone_config.build()),
            # 나머지 거래소도 추가 가능
        ]
        
        # 각 거래소별 핸들러 생성 및 연결 시작
        handlers = []
        for exchange_name, config in exchanges:
            handler = TickerHandler(event_bus, exchange_name)
            logger.info(f"{exchange_name} 핸들러 초기화")
            
            # 비동기 태스크로 연결 시작 (동시에 여러 거래소 연결)
            task = asyncio.create_task(handler.connect_and_subscribe(config))
            handlers.append((handler, task))
        
        # 모든 태스크가 완료될 때까지 대기 (실제로는 무한히 실행되어야 함)
        # 테스트를 위해 5분 후 종료하도록 설정
        await asyncio.sleep(300)  # 5분
        
    finally:
        # 이벤트 버스 종료
        await event_bus.stop()
        logger.info("프로그램 종료")


# 프로그램 실행
if __name__ == "__main__":
    logger.info("티커 구독 프로그램 시작")
    try:
        asyncio.run(run_ticker_subscribers())
    except KeyboardInterrupt:
        logger.info("사용자가 프로그램을 중단했습니다.")
    except Exception as e:
        logger.error(f"예상치 못한 오류: {str(e)}")
