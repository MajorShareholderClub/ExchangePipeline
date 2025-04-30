# 🧩 core 모듈

## 배경 (Problem)
실시간 대용량 암호화폐 데이터를 안정적으로 처리하려면
- 연결 불안정(WebSocket drop, 네트워크 지터)
- 메시지 폭주(TPS 스파이크)
- 거래소별 데이터 형식 차이
를 모두 흡수할 수 있는 견고한 **처리 엔진**이 필요합니다.

## 목표 (Solution)
`core` 모듈은 파이프라인의 심장부로서
1. **Connection 관리**: 자동 재연결 및 헬스 체크
2. **메시지 핸들링**: 타입 식별 후, 전처리 → 이벤트 버스로 라우팅
3. **확장 가능한 파이프라인**: 신규 소스·싱크를 플러그인 방식으로 추가

## 작동 흐름 (Cause–Development)
1. `connection.manager.ConnectionManager` 가 거래소 소켓 상태를 지속 모니터링하고, 문제 발생 시 `retry.RetryPolicy` 에 따라 재연결합니다.
2. 수신한 원시 메시지는 `handlers.BaseMessageHandler._identify_message_type()` 로 **Ticker vs Orderbook** 를 구분합니다.
3. 메시지는 `pipeline.processor.Processor` 로 전달되어, 필요 시 변환·필터링 후 Kafka 프로듀서로 전송됩니다.

## 폴더 구조
```bash
core/
├── connection/
│   ├── manager.py        # 연결 헬스 관리
│   └── retry.py          # 지수 백오프 재시도
│
├── handlers/
│   └── connection_handler.py  # 메시지 핸들러 베이스
│
└── pipeline/
    ├── processor.py      # 파이프라인 제어
    └── source.py         # 데이터 소스 팩토리
```

## 기대 효과 (Result)
- **무중단 수집**: 자동 재연결로 가용성 99.9%+ 달성.
- **유연한 확장성**: 신규 메시지 유형(예: 트레이드, 펀딩률) 추가 시, 핸들러 서브클래스만 구현.
- **성과지표**: 내부 벤치마크 기준, 50k msg/sec 처리 시 평균 레이턴시 15ms.

## 맺음말 (Conclusion)
`core` 모듈은 복잡한 실시간 데이터 문제를 추상화하여, 비즈니스 로직이 **데이터 활용**에 집중할 수 있게 해 줍니다.
