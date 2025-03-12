#!/bin/bash

# 파이프라인 패턴으로 프로젝트 구조 전환 스크립트
# 작성일: 2025-03-12

set -e  # 오류 발생 시 스크립트 중단

BASE_DIR="$(pwd)"
BACKUP_DIR="${BASE_DIR}/backup_$(date +%Y%m%d_%H%M%S)"

echo "===== ExchangePipeline 프로젝트 구조 전환 시작 ====="
echo "현재 디렉토리: ${BASE_DIR}"
echo "백업 디렉토리: ${BACKUP_DIR}"

# 백업 디렉토리 생성
mkdir -p "${BACKUP_DIR}"

# 기존 코드 백업
echo "기존 코드 백업 중..."
cp -r common pipe pipeline protocols config messaging "${BACKUP_DIR}/"
echo "백업 완료: ${BACKUP_DIR}"

# 새 디렉토리 구조 생성
echo "새 디렉토리 구조 생성 중..."

# pipeline 디렉토리 구조 생성
mkdir -p pipeline/core
mkdir -p pipeline/sources/rest/exchanges
mkdir -p pipeline/sources/websocket/exchanges
mkdir -p pipeline/processors/price
mkdir -p pipeline/processors/orderbook
mkdir -p pipeline/sinks

# common 디렉토리 구조 생성
mkdir -p common/models
mkdir -p common/exceptions
mkdir -p common/utils

# config 디렉토리 구조 생성
mkdir -p config/settings

# messaging 디렉토리 구조 생성 (이미 존재할 수 있음)
mkdir -p messaging/kafka
mkdir -p messaging/models

# runners 디렉토리 생성
mkdir -p runners


# 기존 파일 이동 및 구조 조정
echo "기존 파일 이동 및 구조 조정 중..."

# 파일 이동 로직 구현
# 예: WebSocket 관련 파일 이동
if [ -d "pipe" ]; then
  # pipe 디렉토리의 파일을 적절한 위치로 이동
  find pipe -name "*.py" -type f | while read file; do
    # 파일 이름 추출
    filename=$(basename "$file")
    
    # 파일 내용에 따라 적절한 위치로 이동
    if grep -q "WebSocket" "$file" || grep -q "websocket" "$file"; then
      # WebSocket 관련 파일
      cp "$file" "pipeline/sources/websocket/"
      echo "이동: $file -> pipeline/sources/websocket/$filename"
    elif grep -q "connection" "$file"; then
      # 연결 관련 파일
      cp "$file" "pipeline/core/"
      echo "이동: $file -> pipeline/core/$filename"
    fi
  done
fi

# protocols 디렉토리의 파일 이동
if [ -d "protocols" ]; then
  find protocols -name "*.py" -type f | while read file; do
    filename=$(basename "$file")
    
    if grep -q "REST" "$file" || grep -q "rest" "$file"; then
      # REST API 관련 파일
      cp "$file" "pipeline/sources/rest/"
      echo "이동: $file -> pipeline/sources/rest/$filename"
    elif grep -q "WebSocket" "$file" || grep -q "websocket" "$file"; then
      # WebSocket 관련 파일
      cp "$file" "pipeline/sources/websocket/"
      echo "이동: $file -> pipeline/sources/websocket/$filename"
    fi
  done
fi

# common 디렉토리의 파일 이동
if [ -d "common" ]; then
  # 모델 파일 이동
  find common -name "*.py" -type f | grep -i "model" | while read file; do
    filename=$(basename "$file")
    cp "$file" "common/models/"
    echo "이동: $file -> common/models/$filename"
  done
  
  # 유틸리티 파일 이동
  find common -name "*.py" -type f | grep -i "util" | while read file; do
    filename=$(basename "$file")
    cp "$file" "common/utils/"
    echo "이동: $file -> common/utils/$filename"
  done
  
  # 예외 처리 파일 이동
  find common -name "*.py" -type f | grep -i "exception" | while read file; do
    filename=$(basename "$file")
    cp "$file" "common/exceptions/"
    echo "이동: $file -> common/exceptions/$filename"
  done
fi

# config 디렉토리의 파일 이동
if [ -d "config" ]; then
  find config -name "*.py" -type f | while read file; do
    filename=$(basename "$file")
    cp "$file" "config/settings/"
    echo "이동: $file -> config/settings/$filename"
  done
fi

# messaging 디렉토리의 파일 이동
if [ -d "messaging" ]; then
  # Kafka 관련 파일 이동
  find messaging -name "*.py" -type f | grep -i "kafka" | while read file; do
    filename=$(basename "$file")
    cp "$file" "messaging/kafka/"
    echo "이동: $file -> messaging/kafka/$filename"
  done
  
  # 메시지 모델 파일 이동
  find messaging -name "*.py" -type f | grep -i "model" | while read file; do
    filename=$(basename "$file")
    cp "$file" "messaging/models/"
    echo "이동: $file -> messaging/models/$filename"
  done
fi

# 실행 파일 이동
find . -maxdepth 1 -name "*.py" -type f | while read file; do
  filename=$(basename "$file")
  
  # 소켓 또는 파이프라인 실행 관련 파일
  if grep -q "socket" "$file" || grep -q "pipeline" "$file"; then
    cp "$file" "runners/"
    echo "이동: $file -> runners/$filename"
  fi
done

echo "===== 프로젝트 구조 전환 완료 ====="
echo "백업 디렉토리: ${BACKUP_DIR}"
echo "새 구조를 검토하고 필요에 따라 파일을 추가로 이동하거나 수정하세요."
echo "참고: 이 스크립트는 파일을 복사만 했으므로, 원본 파일은 그대로 유지됩니다."
echo "모든 검토가 완료되면 원본 디렉토리를 삭제하고 새 구조로 전환하세요."
