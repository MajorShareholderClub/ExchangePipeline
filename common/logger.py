from __future__ import annotations
import tracemalloc

tracemalloc.start()

from pathlib import Path
import asyncio
import logging
import queue
from logging.handlers import QueueHandler, QueueListener


def ensure_file_exists(file_path: str) -> None:
    """
    주어진 파일 경로에 파일이 존재하지 않으면 새로 생성하고,
    파일이 위치할 폴더가 없으면 폴더를 생성합니다.

    Args:
        file_path (str): 파일 경로
    """
    path = Path(file_path)

    # 파일이 위치할 폴더 경로
    folder_path = path.parent

    # 폴더가 존재하지 않으면 폴더 생성
    if not folder_path.exists():
        folder_path.mkdir(parents=True, exist_ok=True)

    # 파일이 존재하지 않으면 새로 생성
    if not path.exists():
        path.touch()  # 파일 생성


class AsyncLogger:
    def __init__(self, target: str | None = None, folder: str | None = None) -> None:
        """
        로그 수집기 초기화

        Args:
            folder ([str]): 기본 매개변수로 두었으나 파일명 변경 가능
        """
        self.log_queue: queue.Queue = queue.Queue()
        self.target = target
        self.folder: str | None = (
            f"logs/{target}/{folder}/{target}_{folder}.log"
            if target and folder
            else None
        )
        ensure_file_exists(self.folder)

        # handler 초기화
        self.console_handler, self.file_handler = self._setup_handlers()
        self.formatter = self._setup_formatter()

        # formatter 설정
        if self.file_handler:
            self.file_handler.setFormatter(self.formatter)
        self.console_handler.setFormatter(self.formatter)

        self.queue_handler = self._setup_queue_handler()
        self.queue_listener = self._setup_queue_listener()
        self.queue_listener.start()

        self.logger = self._setup_logger()
        self.loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()

    def _setup_queue_handler(self) -> QueueHandler:
        """QueueHandler 초기화"""
        return QueueHandler(self.log_queue)

    def _setup_handlers(
        self,
    ) -> tuple[logging.StreamHandler, logging.FileHandler | None]:
        """콘솔 및 파일 핸들러 초기화"""
        console_handler: logging.StreamHandler = logging.StreamHandler()

        file_handler: logging.FileHandler | None = None
        if self.folder:
            file_handler = logging.FileHandler(self.folder)

        return console_handler, file_handler

    def _setup_formatter(self) -> logging.Formatter:
        """로그 포맷터 초기화"""
        formatter: logging.Formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        return formatter

    def _setup_queue_listener(self) -> QueueListener:
        """QueueListener 초기화"""
        return QueueListener(self.log_queue, self.console_handler, self.file_handler)

    def _setup_logger(self) -> logging.Logger:
        """로거 초기화"""
        logger = logging.getLogger(f"AsyncLogger-{self.target}")
        logger.setLevel(logging.DEBUG)

        # 기존 핸들러 제거
        if logger.hasHandlers():
            logger.handlers.clear()

        logger.addHandler(self.queue_handler)
        return logger

    def get_logger(self) -> logging.Logger:
        """로거 인스턴스 반환"""
        return self.logger

    async def log_message(self, level: int, message: str) -> None:
        """비동기적으로 메시지 로그"""
        logger: logging.Logger = self.get_logger()
        await self.loop.run_in_executor(None, logger.log, level, message)

    def stop(self) -> None:
        """QueueListener 중지 및 리소스 정리"""
        self.queue_listener.stop()

    def __del__(self) -> None:
        """리소스 정리"""
        self.stop()
