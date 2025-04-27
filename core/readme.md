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
│
└── pipeline/             # 데이터 처리 파이프라인
    ├── processor.py      # 메시지 처리 로직
    └── source.py         # 데이터 소스 관리
```

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



