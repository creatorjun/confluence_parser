# infrastructure/app_logger.py
"""애플리케이션 로그 설정.

- 로그 파일: platformdirs user_log_dir 기반 경로
- RotatingFileHandler: 최대 2 MB × 파일 5개 보관
- 콘솔 핸들러: DEBUG 빌드에서만 활성화
- 앱 주요 로거명: 'confluence_parser'
"""
from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from platformdirs import user_log_dir

_APP_NAME   = "SeculayerDocumentParser"
_APP_AUTHOR = "Seculayer"
_LOGGER_NAME = "confluence_parser"

_LOG_FORMAT  = "%(asctime)s [%(levelname)-8s] %(name)s: %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
_MAX_BYTES   = 2 * 1024 * 1024  # 2 MB
_BACKUP_COUNT = 5


def _resolve_log_path() -> Path:
    log_dir = Path(user_log_dir(_APP_NAME, _APP_AUTHOR))
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / "app.log"


def setup_logging(debug: bool = False) -> Path:
    """logging 설정을 초기화하고 로그 파일 경로를 반환한다.

    main.py 에서 한 번만 호출한다.
    """
    log_path = _resolve_log_path()

    root = logging.getLogger()
    root.setLevel(logging.DEBUG if debug else logging.INFO)

    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)

    # 파일 핸들러 — RotatingFileHandler
    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=_MAX_BYTES,
        backupCount=_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    # 콘솔 핸들러 — 개발 실행 시에만 활성화
    if debug or not getattr(sys, "frozen", False):
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)
        root.addHandler(console_handler)

    logging.getLogger(_LOGGER_NAME).info(
        "로그 초기화 완료 — 로그 파일: %s", log_path
    )
    return log_path


def get_logger(name: str | None = None) -> logging.Logger:
    """'하위 로거명'을 포함한 로거를 반환한다.

    사용예)
        log = get_logger(__name__)
        log.info("...")
    """
    child = f"{_LOGGER_NAME}.{name}" if name else _LOGGER_NAME
    return logging.getLogger(child)
