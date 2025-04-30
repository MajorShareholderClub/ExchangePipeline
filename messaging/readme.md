# 🔄 messaging 모듈

## 배경 (Problem)
실시간 스트림을 저장·분배하려면 **높은 처리량·신뢰성**을 제공하는 브로커가 필요합니다.  
Kafka는 훌륭하지만, 프로듀서/컨슈머 설정·모니터링·토픽 관리가 복잡합니다.

## 목표 (Solution)
`messaging` 모듈은 Kafka 사용을 추상화하여
1. **토픽 자동 관리**: 필요 시 토픽 생성/검증
2. **Producer/Consumer 팩토리**: 안전한 기본 파라미터 제공
3. **파티셔닝 전략**: 키 해싱·Composite Key 지원
4. **로컬 개발 스택**: `kafka-docker` 로 단일 명령 배포

## 작동 흐름 (Cause–Development)
1. 파이프라인이 메시지를 보내려면 `data_interaction.get_producer()` 로 프로듀서를 획득.
2. 토픽이 없으면 `data_admin.ensure_topic()` 이 자동 생성합니다.
3. 파티션 키는 `data_partitional.Partitioner` 가 해시를 계산해 균등 분배합니다.
4. 운영자는 `kafka-docker` 의 Grafana/Prometheus 대시보드로 오프셋·TPS를 모니터링합니다.

## 폴더 구조
```bash
messaging/
├── 🐍 data_admin.py        # 데이터 카프카 설정 관리 모듈
├── 🐍 data_interaction.py  # 데이터 카프카 상호작용 모듈
├── 🐍 data_partitional.py  # 데이터 파티션분할 처리 모듈
├── 📂 kafka-docker         # 🐳 Kafka 관련 Docker 설정 파일
│   ├── 🐳 docker_container_remove.sh  # Docker 컨테이너 삭제 스크립트
│   ├── 🐳 fluentd-cluster.yml        # Fluentd 클러스터 설정 파일
│   ├── 📂 jmx_exporter            # JMX Exporter 관련 설정
│   │   ├── 🐳 jmx_prometheus_javaagent-1.0.1.jar # JMX Exporter JAR 파일
│   │   └── 🐳 kafka-broker.yml      # 카프카 broker JVM 설정값들 
│   ├── 🐳 kafka-compose.yml        # Kafka 컴포즈 설정 파일
│   ├── 📂 kui                     # KUI 관련 설정
│   │   └── 🐳 config.yml          # KUI 설정 파일
│   └── 📂 visualization           # 데이터 시각화 관련 파일
│       ├── 📂 grafana            # Grafana 설정 파일
│       └── 📂 prometheus         # Prometheus 관련 설정
│           └── 📂 config          # Prometheus 설정 디렉토리
│               └── 🐳 prometheus.yml  # Prometheus 설정 파일
└── __init__.py

## 기대 효과 (Result)
- **배포 편의성**: `docker-compose up` 으로 로컬 Kafka 클러스터 기동.
- **안정성**: 표준 설정 + 재시도 로직으로 메시지 손실 최소화.
- **운영 가시성**: JMX Exporter + Grafana로 실시간 모니터링.

## 맺음말 (Conclusion)
`messaging` 모듈은 Kafka의 복잡성을 숨기고, 개발자가 **데이터 가치 창출**에 집중하도록 돕습니다.

```bash
# 예시: 토픽 생성 후 메시지 전송
from messaging.data_admin import ensure_topic
from messaging.data_interaction import get_producer

ensure_topic('market.ticker', partitions=12, replication=1)
producer = get_producer()
producer.send('market.ticker', key=b'BTC-USDT', value=b'...')
producer.flush()
