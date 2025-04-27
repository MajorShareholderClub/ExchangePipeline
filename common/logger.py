from __future__ import annotations
import tracemalloc

tracemalloc.start()

from pathlib import Path
import asyncio
import logging
import queue
import sys
from datetime import datetime
from logging.handlers import QueueHandler, QueueListener, TimedRotatingFileHandler
from typing import Any, Optional


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


class PipelineLogger:
    """
    파이프라인 아키텍처에 최적화된 로깅 시스템
    비동기 처리, 컴포넌트별 로깅, 성능 모니터링 기능 제공
    """

    _instances: dict[str, PipelineLogger] = {}
    _default_level = logging.INFO

    @classmethod
    def get_logger(cls, name: str, component: str = None, **kwargs) -> PipelineLogger:
        """
        로거 인스턴스를 반환하는 팩토리 메서드 (싱글톤 패턴 적용)

        Args:
            name: 로거 이름
            component: 컴포넌트 이름 (예: 'exchange', 'event_bus', 'connection')
            **kwargs: 추가 설정

        Returns:
            PipelineLogger: 로거 인스턴스
        """
        key = f"{name}.{component if component else 'root'}"

        if key not in cls._instances:
            cls._instances[key] = cls(name, component, **kwargs)

        return cls._instances[key]

    def __init__(
        self,
        name: str,
        component: str = None,
        level: int = None,
        log_to_file: bool = True,
        log_to_console: bool = True,
        log_dir: str = "logs",
        rotation: str = "midnight",
        location2: str | None = None,
    ):
        """
        로거 초기화

        Args:
            name: 로거 이름
            component: 컴포넌트 이름
            level: 로깅 레벨
            log_to_file: 파일에 로깅 여부
            log_to_console: 콘솔에 로깅 여부
            log_dir: 로그 디렉토리
            rotation: 로그 로테이션 주기
            location2: 로그 파일의 추가 위치
        """
        self.name = name
        self.component = component
        self.level = level or self._default_level
        self.log_to_file = log_to_file
        self.log_to_console = log_to_console
        self.log_dir = log_dir
        self.rotation = rotation
        self.location2: str | None = location2

        # 로깅 큐 및 컨텍스트 초기화 (무제한 버퍼로 설정해 queue.Full 예외 방지)
        self.log_queue: queue.Queue = queue.Queue()  # unlimited buffer
        self.context: dict[str, Any] = {}

        # 로거 및 핸들러 설정
        self._setup_logger(location2)

        # 비동기 이벤트 루프 참조 (필요시 설정)
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def _setup_logger(self, location2: str | None = None) -> None:
        """
        로거, 핸들러, 포맷터 설정
        """
        self.logger_name = (
            f"{self.name}.{self.component}" if self.component else self.name
        )
        self.logger = logging.getLogger(self.logger_name)
        self.logger.setLevel(self.level)

        # 기존 핸들러 제거
        if self.logger.hasHandlers():
            self.logger.handlers.clear()

        # 포맷터 설정
        self.formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - [%(component)s] [%(exchange)s] - %(message)s"
        )

        # 핸들러 설정
        handlers = []

        if self.log_to_console:
            console = logging.StreamHandler(sys.stdout)
            console.setFormatter(self.formatter)
            handlers.append(console)

        if self.log_to_file:
            log_filename = self._get_log_filename(location2=location2)
            ensure_file_exists(log_filename)

            file_handler = TimedRotatingFileHandler(
                filename=log_filename,
                when=self.rotation,
                backupCount=7,  # 7일치 로그 유지
            )
            file_handler.setFormatter(self.formatter)
            handlers.append(file_handler)

        # 큐 핸들러 및 리스너 설정
        self.queue_handler = QueueHandler(self.log_queue)
        self.logger.addHandler(self.queue_handler)

        self.listener = QueueListener(
            self.log_queue, *handlers, respect_handler_level=True
        )
        self.listener.start()

    def _get_log_filename(self, location2: str | None = None) -> str:
        """
        로그 파일 이름 생성
        """
        today = datetime.now().strftime("%Y-%m-%d")
        component_part = f"{self.component}/" if self.component else ""
        # location2가 비어 있지 않으면 로그 디렉토리 바로 아래에 파일을 생성
        path = f"{self.log_dir}"
        if location2 is not None:
            path = f"{path}/{location2}"

        return f"{path}/{component_part}{self.name}_{today}.log"

    def set_context(self, **kwargs) -> None:
        """
        로깅 컨텍스트 설정
        """
        self.context.update(kwargs)

    def clear_context(self) -> None:
        """
        로깅 컨텍스트 초기화
        """
        self.context.clear()

    def _process_message(self, level: int, msg: str, extra: dict = None) -> None:
        """
        메시지 처리 및 로깅
        """
        log_extra = {"component": self.component or "main", "exchange": "global"}

        # 컨텍스트 및 추가 정보 병합
        if self.context:
            log_extra.update(self.context)

        if extra:
            log_extra.update(extra)

        self.logger.log(level, msg, extra=log_extra)

    async def alog(self, level: int, msg: str, **kwargs) -> None:
        """
        비동기적으로 로그 메시지 기록
        """
        if self._loop is None:
            try:
                self._loop = asyncio.get_running_loop()
            except RuntimeError:
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)

        await self._loop.run_in_executor(
            None, self._process_message, level, msg, kwargs
        )

    def debug(self, msg: str, **kwargs) -> None:
        self._process_message(logging.DEBUG, msg, kwargs)

    def info(self, msg: str, **kwargs) -> None:
        self._process_message(logging.INFO, msg, kwargs)

    def warning(self, msg: str, **kwargs) -> None:
        self._process_message(logging.WARNING, msg, kwargs)

    def error(self, msg: str, **kwargs) -> None:
        self._process_message(logging.ERROR, msg, kwargs)

    def critical(self, msg: str, **kwargs) -> None:
        self._process_message(logging.CRITICAL, msg, kwargs)

    async def adebug(self, msg: str, **kwargs) -> None:
        await self.alog(logging.DEBUG, msg, **kwargs)

    async def ainfo(self, msg: str, **kwargs) -> None:
        await self.alog(logging.INFO, msg, **kwargs)

    async def awarning(self, msg: str, **kwargs) -> None:
        await self.alog(logging.WARNING, msg, **kwargs)

    async def aerror(self, msg: str, **kwargs) -> None:
        await self.alog(logging.ERROR, msg, **kwargs)

    async def acritical(self, msg: str, **kwargs) -> None:
        await self.alog(logging.CRITICAL, msg, **kwargs)

    def close(self) -> None:
        """
        리소스 정리
        """
        self.listener.stop()

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass
