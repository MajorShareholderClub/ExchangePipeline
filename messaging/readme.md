### 📂 mq                       # 📊 메시지 큐 관련 모듈
```
├── 🐍 data_admin.py            # 데이터 카프카 설정 관리 모듈
├── 🐍 data_interaction.py      # 데이터 카프카 상호작용 모듈
├── 🐍 data_partitional.py      # 데이터 파티션분할 처리 모듈
├── 📂 kafka-docker             # 🐳 Kafka 관련 Docker 설정 파일
│   ├── 🐳 docker_container_remove.sh  # Docker 컨테이너 삭제 스크립트
│   ├── 🐳 fluentd-cluster.yml        # Fluentd 클러스터 설정 파일
│   ├── 📂 jmx_exporter            # JMX Exporter 관련 설정
│   │   ├── 🐳 jmx_prometheus_javaagent-1.0.1.jar # JMX Exporter JAR 파일
│   │   └── 🐳 kafka-broker.yml      # Kafka 브로커 설정 파일
│   ├── 🐳 kafka-compose.yml        # Kafka 컴포즈 설정 파일
│   ├── 📂 kui                     # KUI 관련 설정
│   │   └── 🐳 config.yml          # KUI 설정 파일
│   ├── 📂 mq                      # Kafka Docker 구성 관련 디렉토리
│   │   └── 📂 kafka-docker        # Kafka Docker 관련 추가 설정
│   │       └── 📂 kui             # KUI 관련 추가 설정
│   │           └── 🐳 config.yml  # KUI 추가 설정 파일
│   └── 📂 visualization           # 데이터 시각화 관련 파일
│       ├── 📂 grafana            # Grafana 설정 파일
│       └── 📂 prometheus         # Prometheus 관련 설정
│           └── 📂 config          # Prometheus 설정 디렉토리
│               └── 🐳 prometheus.yml  # Prometheus 설정 파일
``````