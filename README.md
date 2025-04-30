# Coin Data Stream Processing in Kafka

## 1. 목적 (Purpose)
다양한 암호화폐 거래소의 **실시간 시세·호가 데이터**를 수집·정규화하여 Kafka로 전송함으로써,
백오피스 분석·알고리즘 트레이딩·모니터링 시스템이 즉시 활용할 수 있는 **단일 데이터 레이어**를 제공합니다.

## 2. 폴더 구조 (Directory Layout)
```bash
ExchangePipeline/
├── adapters/     # 거래소별 WebSocket/REST 어댑터
├── common/       # 로깅·예외·설정 등 공통 유틸
├── core/         # 연결 관리·메시지 핸들러·파이프라인 엔진
├── messaging/    # Kafka 토픽 관리·프로듀서/컨슈머 래퍼
├── logs/         # 런타임 로그 출력 디렉터리
├── tests/        # 단위·통합 테스트
├── main.py       # 진입점: 파이프라인 부트스트랩
└── requirements.txt / pyproject.toml
```

## 3. 주요 기능 (Key Features)
- **멀티-익스체인지 지원**: 업비트·바이낸스·크라켄 등 10+ 거래소 어댑터 내장
- **실시간 수집**: asyncio 기반 WebSocket 핸들러로 50k msg/sec 이상 처리
- **Kafka 통합**: 파티셔닝 전략·토픽 자동 생성·프로듀서 재시도 로직 포함
- **높은 가용성**: 자동 재연결, 지수 백오프, 구조화 로그, 예외 통합 처리
- **확장성**: 신규 거래소는 `adapters/exchange/new_exchange.py` 파일만 추가하면 즉시 통합

> 더 자세한 설계 배경·흐름은 각 모듈별 `README.md` 를 참고하세요.



### 시스템 아키텍처 
<img alt="image" src="https://github.com/user-attachments/assets/f2668531-7741-4f74-ab7e-90fd18475bb5" width="800" height="500"/>





