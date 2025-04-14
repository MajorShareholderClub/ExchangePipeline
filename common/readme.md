# 공통 모듈 (Common Module)

## 디렉토리 구조
```
common/
├── data_format.py        # 데이터 변환 및 표준화
├── exceptions.py         # 맞춤형 예외 처리
├── logger.py             # 로깅 시스템
│
├── registry/             # 거래소 및 리소스 등록
│   ├── __init__.py
│   └── exchanges.py      # 거래소 정보 관리
│
└── setting/              # 설정 및 구성 관리
    ├── config/           # 구성 파일
    │   ├── _market_all_ticker.yml   # 거래소별 티커 포맷
    │   └── yml_config.py            # YAML 설정 유틸리티
    │
    ├── parameter/        # 연결 파라미터
    │   ├── connection_parameter.py  # 연결 설정
    │   └── socket_parameter.py      # 소켓 파라미터
    │
    └── types/            # 타입 정의
        ├── __init__.py
        └── _common_exchange.py      # 거래소 공통 타입
```

## 주요 구성 요소

### 1. 데이터 관리
- **data_format.py**: 다양한 거래소 데이터 표준화
- **registry/exchanges.py**: 거래소 메타데이터 관리

### 2. 설정 및 파라미터
```python
# 연결 파라미터 생성 예시
config = create_connection_params(
    region="korea", 
    exchange="upbit", 
    symbol="btc"
)
```

### 3. 티커 포맷 관리
```python
# 거래소별 티커 파라미터 조회
ticker_format = get_ticker_format("upbit")
# ['timestamp', 'opening_price', 'trade_price', ...]
```

## 주요 기능

### 연결 파라미터 빌더
- 유연한 연결 설정 지원
- 거래소/지역별 맞춤 파라미터 구성
- 타임아웃 및 스트림 타입 설정 가능

### 이벤트 기반 아키텍처
- 중앙화된 이벤트 버스
- 연결 재시도 및 장애 처리
- 이벤트 타입: 
  - `CONNECTION_REQUEST`
  - `CONNECTION_RETRY`
  - `CONNECTION_FAILURE`

## 지원 거래소
| 지역   | 거래소     | 상태     | 티커 지원 |
|--------|------------|----------|-----------|
| 한국   | 업비트     | 완료  | 지원   |
| 한국   | 빗썸       | 완료  | 지원   |
| 한국   | 코인원     | 완료  | 지원   |
| 한국   | 코빗       | 완료  | 지원   |
| 아시아 | gateio     | 완료  | 지원   |
| 아시아 | 바이비트   | 완료  | 지원   |
| 아시아 | OKX      | 완료  | 지원   |
| 아시아 | 바이낸스   | 완료  | 지원   |
| 북미   | 크라켄     | 완료  | 지원   |



## 의존성
- Python 3.12+
- PyYAML

## 로드맵
- [ ] 오더북 데이터 표준화  (진행중)
- [ ] 추가 거래소 지원
- [ ] 성능 최적화 및 메모리 관리