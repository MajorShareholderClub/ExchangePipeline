# 🌐 ExchangePipeline Core 모듈

## 📂 디렉토리 구조
```bash
core/
├── connection/           # 연결 관리 및 재시도 로직
│   ├── __init__.py
│   ├── manager.py        # 연결 상태 관리
│   └── retry.py          # 연결 재시도 정책
│
├── handlers/             # 이벤트 및 메시지 핸들러
│   ├── connection_handler.py  # 연결 이벤트 처리
│   └── ticker.py         # 티커 데이터 핸들러
│
└── pipeline/             # 데이터 처리 파이프라인
    ├── processor.py      # 메시지 처리 로직
    └── source.py         # 데이터 소스 관리
```

## 🚀 핵심 기능

### 1. 연결 관리 시스템
```python
# 연결 재시도 정책 예시
class ConnectionRetryPolicy:
    def execute(self, exchange: str):
        retry_count = 0
        while retry_count < MAX_RETRIES:
            try:
                # 연결 시도
                connect(exchange)
                break
            except ConnectionError:
                retry_count += 1
                wait_time = exponential_backoff(retry_count)
                time.sleep(wait_time)
```

### 2. 이벤트 기반 메시지 처리
```python
# 메시지 라우팅 로직
def route_message(raw_data: dict):
    msg_type = _identify_message_type(raw_data)
    if msg_type == MessageType.TICKER:
        TickerHandler.process(raw_data)
    elif msg_type == MessageType.ORDERBOOK:
        OrderbookHandler.queue(raw_data)
```

## 🔧 주요 컴포넌트

### 연결 관리자 (Connection Manager)
- 거래소 연결 상태 모니터링
- 자동 재연결 메커니즘
- 연결 실패 시 이벤트 발행

### 메시지 핸들러
- 티커 데이터 처리
- 메시지 유형 식별
- 이벤트 버스와 통합

### 데이터 파이프라인
- 메시지 변환 및 라우팅
- 데이터 소스 추상화
- 확장 가능한 처리 아키텍처

## 📊 구현 현황
| 컴포넌트          | 진행도 | 상세 현황                     |
|--------------------|--------|-------------------------------|
| 연결 재시도 정책   | 95%    | 지수 백오프 구현              |
| 메시지 라우팅      | 90%    | 티커/오더북 처리              |
| 이벤트 핸들러      | 85%    | 대부분의 이벤트 유형 지원     |

## 🛠 고급 기능
- 동적 재시도 전략
- 멀티스레드 안전 연결 관리
- 확장 가능한 메시지 처리 아키텍처

## 🔗 의존성
- Python 3.9+
- asyncio
- pydantic
- loguru

## 📝 로드맵
- [ ] 고급 오류 처리 메커니즘
- [ ] 성능 최적화
- [ ] 추가 메시지 유형 지원

## 🤝 기여 가이드라인
1. 새로운 메시지 핸들러 추가 시:
   - `handlers/` 디렉토리에 새 핸들러 구현
   - 기본 메시지 처리 인터페이스 준수
2. 연결 재시도 정책 확장
3. 일관된 로깅 및 오류 처리

> 📘 **아키텍처 원칙**: 
> - 모듈성 유지
> - 최소 의존성 원칙
> - 이벤트 기반 아키텍처 준수
