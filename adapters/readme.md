# 📦 adapters 모듈

## 배경 (Problem)
거래소마다 웹소켓/REST API 규격, 인증 방식, 데이터 포맷이 제각각입니다.  
이질적인 인터페이스를 직접 처리하면 파이프라인이 복잡해지고 유지보수가 어려워집니다.

## 목표 (Solution)
`adapters` 모듈은 **어댑터 패턴**으로 거래소별 API를 추상화하여
“단일 내부 표준”(`Ticker`, `Orderbook` Pydantic 모델)로 변환합니다.

## 작동 흐름 (Cause–Development)
1. `BaseWebsocketHandler` / `BaseRestAdapter` 가 공통 기능(연결, 재시도, 시리얼라이즈)을 정의합니다.
2. `exchange/*.py` 파일이 거래소별 세부 로직(구독 메시지, 시그니처, Ping/Pong 등)을 오버라이드합니다.
3. 변환된 표준 메시지는 `core.pipeline` 으로 전달되어 후속 처리를 거칩니다.

## 폴더 구조
```bash
adapters/
├── base/
│   ├── websocket.py   # WebSocket 공통 핸들러
│   └── rest.py        # REST 전용 기본 어댑터
├── exchange/
│   ├── binance.py     # Binance WebSocket 어댑터
│   ├── kraken.py
│   ├── upbit.py
│   └── ...
└── utils.py           # 시리얼라이저·헬퍼 함수
```

## 기대 효과 (Result)
- **단일 코드 경로**: 신규 거래소 추가 시 `exchange/new_exchange.py` 만 작성하면 끝.
- **유지보수성**: 공통 재연결·예외 로직을 한 곳에서 관리.
- **테스트 용이성**: Base 클래스 단위 테스트로 전체 커버리지 확보 가능.

## 맺음말 (Conclusion)
`adapters` 모듈은 “거래소 다양성”이라는 난제를 추상화 계층으로 해결하여,
핵심 파이프라인을 **단순·확장 가능**하게 만듭니다.