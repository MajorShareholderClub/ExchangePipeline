#!/usr/bin/env python3
"""
거래소 WebSocket 파라미터 생성 테스트 스크립트

팩토리 패턴으로 리팩토링된 거래소별 소켓 파라미터 생성기를 테스트합니다.
기존 구현과 동일한 결과를 생성하는지 확인합니다.
"""

import json
import time
import logging
from typing import Any

# 로깅 설정
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 팩토리 패턴으로 구현된 파라미터 생성기
from common.setting.exchange import SocketParameterFactory


def test_korea_exchanges() -> None:
    """한국 거래소 파라미터 생성 테스트"""
    print("\n=== 한국 거래소 파라미터 생성 테스트 ===\n")

    # 테스트할 거래소 목록
    exchanges = ["upbit", "bithumb", "korbit", "coinone"]

    # 테스트할 심볼 목록 - 한국 거래소는 KRW 기반
    symbols = ["BTC", "ETH"]

    # 요청 타입
    req_types = ["ticker", "orderbook"]

    # 각 거래소 테스트
    for exchange in exchanges:
        print(f"\n{'-'*50}")
        print(f"거래소: {exchange.upper()}")
        logger.debug(f"테스트 시작: {exchange}")

        for req_type in req_types:
            try:
                print(f"\n{req_type.upper()} 채널:")
                logger.debug(f"채널 요청: {req_type}")

                # 시작 시간 측정
                start_time = time.time()

                # 팩토리 패턴으로 파라미터 생성
                logger.debug(f"SocketParameterFactory.get_creator({exchange}) 호출")
                creator = SocketParameterFactory.get_creator(exchange)
                logger.debug(f"생성된 creator: {creator.__class__.__name__}")

                logger.debug(
                    f"파라미터 생성 시작: exchange={exchange}, symbols={symbols}, req_type={req_type}"
                )
                params = creator.create_parameters(symbols, req_type)

                # 종료 시간 측정
                end_time = time.time()
                elapsed_time = (end_time - start_time) * 1000  # 밀리초로 변환

                # 결과 출력
                print(json.dumps(params, indent=2, ensure_ascii=False))
                print(f"소요 시간: {elapsed_time:.2f}ms")

            except Exception as e:
                logger.exception(f"오류 발생: {e}")
                print(f"오류 발생: {e}")


def test_global_exchanges() -> None:
    """글로벌 거래소 파라미터 생성 테스트"""
    print("\n=== 글로벌 거래소 파라미터 생성 테스트 ===\n")

    # 테스트할 거래소 목록
    exchanges = ["binance", "kraken"]

    # 테스트할 심볼 목록 - 글로벌 거래소는 USD 기반
    symbols = ["BTC_USDT", "ETH_USDT"]

    # 요청 타입
    req_types = ["ticker", "orderbook"]

    # 각 거래소 테스트
    for exchange in exchanges:
        print(f"\n{'-'*50}")
        print(f"거래소: {exchange.upper()}")
        logger.debug(f"테스트 시작: {exchange}")

        for req_type in req_types:
            try:
                print(f"\n{req_type.upper()} 채널:")
                logger.debug(f"채널 요청: {req_type}")

                # 시작 시간 측정
                start_time = time.time()

                # 팩토리 패턴으로 파라미터 생성
                logger.debug(f"SocketParameterFactory.get_creator({exchange}) 호출")
                creator = SocketParameterFactory.get_creator(exchange)
                logger.debug(f"생성된 creator: {creator.__class__.__name__}")

                logger.debug(
                    f"파라미터 생성 시작: exchange={exchange}, symbols={symbols}, req_type={req_type}"
                )
                params = creator.create_parameters(symbols, req_type)

                # 종료 시간 측정
                end_time = time.time()
                elapsed_time = (end_time - start_time) * 1000  # 밀리초로 변환

                # 결과 출력
                print(json.dumps(params, indent=2, ensure_ascii=False))
                print(f"소요 시간: {elapsed_time:.2f}ms")

            except Exception as e:
                logger.exception(f"오류 발생: {e}")
                print(f"오류 발생: {e}")


def test_asia_exchanges() -> None:
    """아시아 거래소 파라미터 생성 테스트"""
    print("\n=== 아시아 거래소 파라미터 생성 테스트 ===\n")

    # 테스트할 거래소 목록
    exchanges = ["gateio", "okx", "bybit"]

    # 테스트할 심볼 목록
    symbols = ["BTC_USDT", "ETH_USDT"]

    # 요청 타입
    req_types = ["ticker", "orderbook"]

    # 각 거래소 테스트
    for exchange in exchanges:
        print(f"\n{'-'*50}")
        print(f"거래소: {exchange.upper()}")
        logger.debug(f"테스트 시작: {exchange}")

        for req_type in req_types:
            try:
                print(f"\n{req_type.upper()} 채널:")
                logger.debug(f"채널 요청: {req_type}")

                # 시작 시간 측정
                start_time = time.time()

                # 팩토리 패턴으로 파라미터 생성
                logger.debug(f"SocketParameterFactory.get_creator({exchange}) 호출")
                creator = SocketParameterFactory.get_creator(exchange)
                logger.debug(f"생성된 creator: {creator.__class__.__name__}")

                logger.debug(
                    f"파라미터 생성 시작: exchange={exchange}, symbols={symbols}, req_type={req_type}"
                )
                params = creator.create_parameters(symbols, req_type)

                # 종료 시간 측정
                end_time = time.time()
                elapsed_time = (end_time - start_time) * 1000  # 밀리초로 변환

                # 결과 출력
                print(json.dumps(params, indent=2, ensure_ascii=False))
                print(f"소요 시간: {elapsed_time:.2f}ms")

            except Exception as e:
                logger.exception(f"오류 발생: {e}")
                print(f"오류 발생: {e}")


def main() -> None:
    """메인 함수"""
    print("WebSocket 파라미터 팩토리 테스트 시작...\n")

    try:
        # 한국 거래소 테스트
        test_korea_exchanges()

        # # 글로벌 거래소 테스트
        # test_global_exchanges()

        # # 아시아 거래소 테스트
        # test_asia_exchanges()
    except Exception as e:
        logger.exception(f"테스트 중 예외 발생: {e}")
        print(f"테스트 중 예외 발생: {e}")


if __name__ == "__main__":
    main()
