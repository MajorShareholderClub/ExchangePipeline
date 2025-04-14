# 거래소 어댑터 모듈

## 📂 디렉토리 구조
```
adapters/
├── base/                 # 기본 클래스 및 인터페이스
│   ├── event/            # 이벤트 버스 구현
│   ├── interface/        # REST/웹소켓 인터페이스
│   └── async_api_client.py
└── exchange/             # 거래소별 구현
    ├── asia/             # 아시아 거래소
    │   ├── binance.py
    │   ├── bybit.py
    │   └── okx.py
    ├── korea/            # 국내 거래소
    │   ├── upbit.py
    │   ├── bithumb.py
    │   └── coinone.py
    └── ne/               # 비아시아권 거래소
        └── kraken.py
```

## 🧩 주요 구성 요소

### 기본 클래스
1. **BaseWebsocketHandler**
    - 하트비트 관리
    - 메시지 루프 처리
    - 연결 재시도 로직

2. **BaseAsiaEuropeHandler**
    - 핑-퐁 메커니즘
    - 공통 메시지 처리
    ```python
    class BaseAsiaEuropeHandler(BaseWebsocketHandler):
        async def _handle_message_loop(self, websocket, timeout):
            # 공통 메시지 루프 로직
    ```

3. **BaseKoreaWebsocketHandler**
    - 국내 거래소 특화 처리
    - 티커 데이터 처리

### 거래소 구현체
| 거래소  | 핸들러 클래스             | 하트비트 |
|---------|--------------------------|----------|
| 바이낸스  | BinanceWebsocketHandler  | 30초     |
| 업비트   | UpbitWebsocketHandler    | 커스텀   |
| 크라켄   | KrakenWebsocketHandler   | 30초     |
| 빗썸     | BithumbWebsocketHandler  | 커스텀   |
| 코빗     | KorbitWebsocketHandler   | 커스텀   |
| 코인원    | CoinoneWebsocketHandler  | 커스텀   |
| gateio  | GateioWebsocketHandler   | 20초     |
| 바이비트  | BybitWebsocketHandler  | 30초     |

## 🔌 이벤트 버스 연동
```python
# 초기화 예시
from adapters.base.event.event_bus import EventBus
from adapters.exchange import BinanceWebsocketHandler

handler = BinanceWebsocketHandler(event_bus=EventBus(), exchange_name="Binance")
```

## ♻️ 연결 관리
- 자동 재연결
- 설정 가능한 재시도 정책
- 하트비트 모니터링

## 📝 기여 가이드라인
1. 적절한 지역 디렉토리에 새 핸들러 생성
2. 기본 클래스 상속
    - `BaseAsiaEuropeHandler` 또는 `BaseKoreaWebsocketHandler` 상속
3. 필수 메서드 구현:
    - `_send_heartbeat()`
    - `_parse_message()`
4. 하트비트 설정
    - `self.heartbeat_interval` 설정
5. 이벤트 버스 연동
    - `event_bus` 인스턴스 전달

```python
class NewExchangeHandler(BaseAsiaEuropeHandler):
    def __init__(self, event_bus, exchange_name):
        super().__init__(event_bus, exchange_name)
        self.heartbeat_interval = 25  # 25초 간격
```