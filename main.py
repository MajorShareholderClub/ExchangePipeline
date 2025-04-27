import asyncio
import argparse
import signal


# 연결 관리 임포트
from core.connection import run_all_exchanges
from common.logger import PipelineLogger
from common.registry.exchanges import EXCHANGE_HANDLERS

# 메인 애플리케이션 로거
main_logger = PipelineLogger.get_logger("pipeline", "main")


def parse_arguments() -> argparse.Namespace:
    """명령줄 인수 파싱 함수"""
    parser = argparse.ArgumentParser(description="거래소 WebSocket 구독 프로그램")

    parser.add_argument(
        "--type",
        "-t",
        choices=["ticker", "orderbook"],
        default="ticker",
        help="구독할 데이터 타입 (기본값: ticker)",
    )

    parser.add_argument(
        "--exchanges",
        "-e",
        nargs="*",
        help="구독할 거래소 목록 (공백으로 구분, 기본값: 모든 거래소)",
    )

    parser.add_argument(
        "--symbols",
        "-s",
        nargs="*",
        default=["BTC", "ETH"],
        help="구독할 심볼 목록 (공백으로 구분, 기본값: BTC ETH)",
    )

    parser.add_argument(
        "--list-exchanges", action="store_true", help="지원되는 모든 거래소 목록 출력"
    )

    return parser.parse_args()


def setup_signal_handlers(loop: asyncio.AbstractEventLoop) -> None:
    """시그널 핸들러 설정 (스무스한 종료 처리)"""
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown(loop)))


async def shutdown(loop: asyncio.AbstractEventLoop) -> None:
    """프로그램 종료 처리"""
    main_logger.info("프로그램 종료 중...")

    # 현재 실행 중인 모든 태스크 종료
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]

    for task in tasks:
        task.cancel()

    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()
    main_logger.info("프로그램이 안전하게 종료되었습니다.")


async def main() -> None:
    """메인 실행 함수"""
    args = parse_arguments()

    # 지원 거래소 목록 출력 옵션
    if args.list_exchanges:
        main_logger.info("지원되는 거래소 목록:")
        for exchange in sorted(EXCHANGE_HANDLERS.keys()):
            main_logger.info(f"- {exchange}")
        return

    request_type = args.type
    exchanges = args.exchanges
    symbols = args.symbols

    main_logger.info(f"구독 타입: {request_type}")
    main_logger.info(f"대상 거래소: {exchanges if exchanges else '모든 거래소'}")
    main_logger.info(f"대상 심볼: {symbols}")

    # 이벤트 루프 및 시그널 핸들러 설정
    loop = asyncio.get_running_loop()

    try:
        main_logger.info("WebSocket 연결 시작...")
        await run_all_exchanges(request_type, exchanges, symbols)
    except KeyboardInterrupt:
        main_logger.info("사용자가 프로그램을 중단했습니다.")
        setup_signal_handlers(loop)
    except Exception as e:
        main_logger.error(f"예상치 못한 오류: {str(e)}")


if __name__ == "__main__":
    main_logger.info("=== 거래소 WebSocket 구독 프로그램 시작 ===")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n프로그램이 종료되었습니다.")
    except Exception as e:
        main_logger.error(f"프로그램 실행 중 오류 발생: {str(e)}")
