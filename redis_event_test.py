import asyncio
import logging
import json
from datetime import datetime

from adapters.base.event.types import EventType
from adapters.base.event.event_bus import EventBus

# 로깅 설정
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)

# 이벤트 핸들러
async def price_update_handler(data):
    print(f"가격 업데이트 수신: {data}")
    return None

async def trade_handler(data):
    print(f"거래 이벤트 수신: {data}")
    await asyncio.sleep(0.1)  # 약간의 처리 시간 흉내
    return None

async def system_event_handler(data):
    print(f"시스템 이벤트 수신: {data}")
    return None

# 메인 함수
async def main():
    print("Redis 기반 분산 이벤트 시스템 테스트 시작")
    
    # EventBus 인스턴스 생성 (Redis 연결)
    event_bus = EventBus(redis_url="redis://localhost:6379/0")
    await event_bus.initialize()
    
    try:
        # 이벤트 핸들러 등록
        await event_bus.subscribe(EventType.PRICE_UPDATE, price_update_handler)
        await event_bus.subscribe(EventType.TRADE, trade_handler)
        await event_bus.subscribe(EventType.SYSTEM_INFO, system_event_handler)
        
        print("모든 이벤트 핸들러 등록 완료")
        
        # 시스템 시작 이벤트 발행
        await event_bus.start()
        
        # 테스트 이벤트 발행
        print("\n테스트 이벤트 발행 시작")
        
        # 가격 업데이트 이벤트
        for i in range(3):
            price_data = {
                "exchange": "binance",
                "symbol": "BTC/USDT",
                "price": 50000 + (i * 100),
                "timestamp": datetime.now().isoformat()
            }
            await event_bus.publish(EventType.PRICE_UPDATE, price_data)
            print(f"가격 업데이트 이벤트 #{i+1} 발행")
            await asyncio.sleep(0.5)
        
        # 거래 이벤트
        trade_data = {
            "exchange": "upbit",
            "symbol": "ETH/KRW",
            "amount": 1.5,
            "price": 3500000,
            "side": "buy",
            "timestamp": datetime.now().isoformat()
        }
        await event_bus.publish(EventType.TRADE, trade_data)
        print("거래 이벤트 발행")
        
        # 시스템 이벤트
        system_data = {
            "message": "시스템 상태 양호",
            "uptime": 3600,
            "memory_usage": "23%"
        }
        await event_bus.publish(EventType.SYSTEM_INFO, system_data)
        print("시스템 이벤트 발행")
        
        # 이벤트 처리 완료 대기
        print("\n이벤트 처리 완료 대기 중...")  
        await asyncio.sleep(2)
        
    finally:
        # 종료 정리
        print("\n이벤트 버스 종료 중...")  
        await event_bus.stop()
        print("테스트 완료")

# 비동기 메인 실행
if __name__ == "__main__":
    asyncio.run(main())
