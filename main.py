import asyncio
import logging

# 연결 관리 임포트
from core.connection import run_all_exchanges
from common.logger import PipelineLogger

# 로깅 설정
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("ticker_subscriber")

# 메인 애플리케이션 로거
main_logger = PipelineLogger.get_logger("pipeline", "main")


# 프로그램 실행
if __name__ == "__main__":
    main_logger.info("티커 구독 프로그램 시작")
    try:
        # 특정 거래소만 실행하려면 리스트에 추가 (비어있으면 모든 거래소 실행)
        exchanges_to_run = []
        main_logger.info("연결 관리 시작")
        asyncio.run(run_all_exchanges(exchanges_to_run))
    except KeyboardInterrupt:
        main_logger.info("사용자가 프로그램을 중단했습니다.")
    except Exception as e:
        main_logger.error(f"예상치 못한 오류: {str(e)}")
