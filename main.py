# main.py
from __future__ import annotations

import sys

try:
    import ctypes
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
        "com.confluence.parser.gui"
    )
except Exception:
    pass

from PyQt6.QtWidgets import QApplication

from infrastructure.app_logger import get_logger, setup_logging
from infrastructure.app_settings_store import JsonAppSettingsStore
from infrastructure.credential_store import SecureCredentialStore
from infrastructure.confluence_repository import ConfluenceRepository
from infrastructure.converters.md_converter import MdConverter
from infrastructure.converters.docx_converter import DocxConverter
from infrastructure.converters.excel_converter import ExcelConverter
from infrastructure.converters.pdf_converter import PdfConverter
from view.main_window import MainWindow
from view.theme import QSS
from viewmodel.main_viewmodel import MainViewModel


def main() -> None:
    # 로그 초기화 — Composition Root 첫 줄
    log_path = setup_logging()
    log = get_logger(__name__)
    log.info("=== Seculayer Document Parser 시작 ===")
    log.info("로그 파일: %s", log_path)

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName("Seculayer Document Parser")
    app.setOrganizationName("Seculayer")
    app.setStyleSheet(QSS)

    cred_store     = SecureCredentialStore()
    settings_store = JsonAppSettingsStore()
    email, token   = cred_store.load()
    repo           = ConfluenceRepository(email, token)
    log.info("인증 정보 로드: email=%s, token=%s",
             email or "(없음)", "***" if token else "(없음)")

    converters = {
        "md":   MdConverter(),
        "docx": DocxConverter(),
        "xlsx": ExcelConverter(),
        "pdf":  PdfConverter(),
    }

    viewmodel = MainViewModel(
        credential_store=cred_store,
        converters=converters,
        repo=repo,
        settings_store=settings_store,
    )

    win = MainWindow(viewmodel)
    win.show()
    log.info("메인 윈도우 표시 완료")

    exit_code = app.exec()
    log.info("=== 앱 종료 (exit_code=%d) ===", exit_code)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
