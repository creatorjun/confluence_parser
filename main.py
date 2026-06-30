"""Confluence Parser — 진입점

실행:
    python main.py

구조 (MVVM):
    main.py                      ← 진입점
    viewmodel/main_viewmodel.py  ← ViewModel  (상태 + 비즈니스 로직)
    viewmodel/settings_viewmodel.py
    view/main_window.py          ← View       (UI, 이벤트 바인딩)
    view/settings_dialog.py
    view/theme.py                ← QSS 테마 상수
    view/widgets.py              ← 공용 위젯 헬퍼
    worker.py                    ← QThread 백그라운드 워커
    confluence_client.py         ← Model      (REST API)
    config.py                    ← .env 로더/저장
"""
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

from view.main_window import MainWindow
from view.theme import QSS


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName("Confluence Parser")
    app.setOrganizationName("confluence-parser")
    app.setStyleSheet(QSS)

    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
