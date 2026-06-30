# gui.py
"""
Confluence Parser - PyQt6 GUI 메인

아키텍처:
  gui.py           - View (PyQt6 위젯)
  worker.py        - Worker (QThread, 백그라운드 변환)
  confluence_client.py - Model (API 통신)
  converters/      - 각 포맷 변환기
  html_cleaner.py  - HTML 정제
  config.py        - .env 설정 로더/저장
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QIcon, QPalette, QColor, QPixmap
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QCheckBox,
    QComboBox, QTextEdit, QProgressBar,
    QFileDialog, QDialog, QDialogButtonBox,
    QMessageBox, QFrame, QSizePolicy,
    QGroupBox, QSpacerItem,
)

import config
from worker import ConvertWorker


# ─────────────────────────────────────────────
# 팔레트 / 스타일
# ─────────────────────────────────────────────
_DARK_BG   = "#1e1e2e"
_SURFACE   = "#2a2a3e"
_SURFACE2  = "#313148"
_ACCENT    = "#7c6af7"
_ACCENT2   = "#9c8cf9"
_TEXT      = "#cdd6f4"
_MUTED     = "#a6adc8"
_SUCCESS   = "#a6e3a1"
_ERROR     = "#f38ba8"
_WARN      = "#fab387"
_BORDER    = "#45475a"

_QSS = f"""
QMainWindow, QDialog {{
    background: {_DARK_BG};
}}
QWidget {{
    background: {_DARK_BG};
    color: {_TEXT};
    font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif;
    font-size: 13px;
}}
QGroupBox {{
    background: {_SURFACE};
    border: 1px solid {_BORDER};
    border-radius: 8px;
    margin-top: 12px;
    padding: 12px 10px 10px 10px;
    font-weight: bold;
    color: {_TEXT};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 4px;
}}
QLineEdit {{
    background: {_SURFACE2};
    border: 1px solid {_BORDER};
    border-radius: 6px;
    padding: 8px 12px;
    color: {_TEXT};
    selection-background-color: {_ACCENT};
}}
QLineEdit:focus {{
    border: 1px solid {_ACCENT};
}}
QComboBox {{
    background: {_SURFACE2};
    border: 1px solid {_BORDER};
    border-radius: 6px;
    padding: 8px 12px;
    color: {_TEXT};
    min-width: 120px;
}}
QComboBox::drop-down {{
    border: none;
    width: 24px;
}}
QComboBox::down-arrow {{
    width: 12px; height: 12px;
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {_MUTED};
}}
QComboBox QAbstractItemView {{
    background: {_SURFACE2};
    border: 1px solid {_BORDER};
    color: {_TEXT};
    selection-background-color: {_ACCENT};
    padding: 4px;
}}
QPushButton {{
    background: {_ACCENT};
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 9px 20px;
    font-weight: bold;
    font-size: 13px;
}}
QPushButton:hover {{
    background: {_ACCENT2};
}}
QPushButton:pressed {{
    background: #6a58e0;
}}
QPushButton:disabled {{
    background: {_BORDER};
    color: {_MUTED};
}}
QPushButton#btn_secondary {{
    background: {_SURFACE2};
    color: {_TEXT};
    border: 1px solid {_BORDER};
}}
QPushButton#btn_secondary:hover {{
    background: {_SURFACE};
    border-color: {_ACCENT};
}}
QPushButton#btn_danger {{
    background: #e05c7a;
}}
QPushButton#btn_danger:hover {{
    background: #f38ba8;
}}
QCheckBox {{
    spacing: 8px;
    color: {_TEXT};
    background: transparent;
}}
QCheckBox::indicator {{
    width: 18px; height: 18px;
    border: 2px solid {_BORDER};
    border-radius: 4px;
    background: {_SURFACE2};
}}
QCheckBox::indicator:checked {{
    background: {_ACCENT};
    border-color: {_ACCENT};
}}
QTextEdit {{
    background: {_SURFACE2};
    border: 1px solid {_BORDER};
    border-radius: 6px;
    padding: 8px;
    color: {_TEXT};
    font-family: 'Consolas', 'D2Coding', monospace;
    font-size: 12px;
}}
QProgressBar {{
    background: {_SURFACE2};
    border: 1px solid {_BORDER};
    border-radius: 6px;
    height: 10px;
    text-align: center;
    color: transparent;
}}
QProgressBar::chunk {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                stop:0 {_ACCENT}, stop:1 {_ACCENT2});
    border-radius: 6px;
}}
QLabel#lbl_title {{
    font-size: 22px;
    font-weight: bold;
    color: {_ACCENT2};
    background: transparent;
}}
QLabel#lbl_sub {{
    font-size: 12px;
    color: {_MUTED};
    background: transparent;
}}
QLabel#lbl_status_ok  {{ color: {_SUCCESS}; background: transparent; font-weight: bold; }}
QLabel#lbl_status_err {{ color: {_ERROR};   background: transparent; font-weight: bold; }}
QFrame#divider {{
    background: {_BORDER};
    max-height: 1px;
    border: none;
}}
"""


# ─────────────────────────────────────────────
# 설정 다이얼로그
# ─────────────────────────────────────────────
class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚙ 설정 - Confluence 인증 정보")
        self.setMinimumWidth(480)
        self.setStyleSheet(_QSS)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(24, 24, 24, 24)

        layout.addWidget(QLabel("Confluence 이메일 주소"))
        self.le_email = QLineEdit(config.get("CONFLUENCE_EMAIL"))
        self.le_email.setPlaceholderText("example@company.com")
        layout.addWidget(self.le_email)

        layout.addWidget(QLabel("Confluence API Token"))
        self.le_token = QLineEdit(config.get("CONFLUENCE_API_TOKEN"))
        self.le_token.setPlaceholderText("Atlassian API Token")
        self.le_token.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.le_token)

        hint = QLabel(
            '💡 API Token 발급: '
            '<a href="https://id.atlassian.com/manage-profile/security/api-tokens" '
            'style="color:#7c6af7;">Atlassian Account 보안 설정</a>'
        )
        hint.setOpenExternalLinks(True)
        hint.setObjectName("lbl_sub")
        layout.addWidget(hint)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self._save)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _save(self):
        email = self.le_email.text().strip()
        token = self.le_token.text().strip()
        if not email or not token:
            QMessageBox.warning(self, "입력 오류", "이메일과 API Token을 모두 입력해 주세요.")
            return
        config.save(email, token)
        self.accept()


# ─────────────────────────────────────────────
# 메인 윈도우
# ─────────────────────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Confluence Parser")
        self.setMinimumSize(780, 620)
        self.resize(900, 700)
        self.setStyleSheet(_QSS)
        self._worker: ConvertWorker | None = None
        self._build_ui()
        self._check_credentials()

    # ── UI 구성 ──────────────────────────────
    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        main_layout = QVBoxLayout(root)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(16)

        # 헤더
        hdr = QHBoxLayout()
        lbl_title = QLabel("📄 Confluence Parser")
        lbl_title.setObjectName("lbl_title")
        hdr.addWidget(lbl_title)
        hdr.addStretch()
        self.lbl_cred = QLabel()
        hdr.addWidget(self.lbl_cred)
        btn_settings = QPushButton("⚙ 설정")
        btn_settings.setObjectName("btn_secondary")
        btn_settings.setFixedWidth(90)
        btn_settings.clicked.connect(self._open_settings)
        hdr.addWidget(btn_settings)
        main_layout.addLayout(hdr)

        # 구분선
        divider = QFrame()
        divider.setObjectName("divider")
        divider.setFrameShape(QFrame.Shape.HLine)
        main_layout.addWidget(divider)

        # ── 입력 그룹 ──
        grp_input = QGroupBox("변환 설정")
        grid = QGridLayout(grp_input)
        grid.setSpacing(10)
        grid.setContentsMargins(14, 18, 14, 14)

        grid.addWidget(QLabel("Confluence 페이지 URL"), 0, 0, 1, 4)
        self.le_url = QLineEdit()
        self.le_url.setPlaceholderText(
            "https://your-instance.atlassian.net/wiki/spaces/SPACE/pages/123456/..."
        )
        grid.addWidget(self.le_url, 1, 0, 1, 4)

        grid.addWidget(QLabel("출력 형식"), 2, 0)
        self.cb_format = QComboBox()
        self.cb_format.addItems(["Markdown (.md)", "Word (.docx)", "Excel (.xlsx)", "PDF (.pdf)"])
        self.cb_format.setFixedWidth(180)
        grid.addWidget(self.cb_format, 2, 1)

        self.chk_children = QCheckBox("하위 문서 포함")
        self.chk_children.setChecked(True)
        grid.addWidget(self.chk_children, 2, 2)

        grid.addWidget(QLabel("저장 경로"), 3, 0)
        self.le_out = QLineEdit(str(Path.home() / "output.md"))
        grid.addWidget(self.le_out, 3, 1, 1, 2)
        btn_browse = QPushButton("📂 찾기")
        btn_browse.setObjectName("btn_secondary")
        btn_browse.setFixedWidth(80)
        btn_browse.clicked.connect(self._browse)
        grid.addWidget(btn_browse, 3, 3)

        self.cb_format.currentIndexChanged.connect(self._sync_extension)
        main_layout.addWidget(grp_input)

        # ── 실행 버튼 ──
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.btn_run = QPushButton("▶  변환 시작")
        self.btn_run.setFixedHeight(42)
        self.btn_run.setMinimumWidth(160)
        self.btn_run.clicked.connect(self._start)
        btn_row.addWidget(self.btn_run)
        self.btn_stop = QPushButton("■  중단")
        self.btn_stop.setObjectName("btn_danger")
        self.btn_stop.setFixedHeight(42)
        self.btn_stop.setMinimumWidth(100)
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self._stop)
        btn_row.addWidget(self.btn_stop)
        main_layout.addLayout(btn_row)

        # ── 진행률 ──
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(10)
        main_layout.addWidget(self.progress_bar)

        # ── 로그 ──
        grp_log = QGroupBox("진행 로그")
        log_layout = QVBoxLayout(grp_log)
        log_layout.setContentsMargins(10, 14, 10, 10)
        self.te_log = QTextEdit()
        self.te_log.setReadOnly(True)
        self.te_log.setMinimumHeight(180)
        log_layout.addWidget(self.te_log)

        log_btns = QHBoxLayout()
        log_btns.addStretch()
        btn_clear = QPushButton("로그 지우기")
        btn_clear.setObjectName("btn_secondary")
        btn_clear.setFixedWidth(100)
        btn_clear.clicked.connect(self.te_log.clear)
        log_btns.addWidget(btn_clear)
        log_layout.addLayout(log_btns)
        main_layout.addWidget(grp_log)

        # ── 상태바 ──
        self.lbl_status = QLabel("대기 중")
        self.lbl_status.setObjectName("lbl_sub")
        self.statusBar().addWidget(self.lbl_status)

    # ── 슬롯 ────────────────────────────────
    def _check_credentials(self):
        email = config.get("CONFLUENCE_EMAIL")
        if email:
            self.lbl_cred.setText(f"✅ {email}")
            self.lbl_cred.setObjectName("lbl_status_ok")
        else:
            self.lbl_cred.setText("⚠ 인증 정보 없음")
            self.lbl_cred.setObjectName("lbl_status_err")
        # 스타일 재적용
        self.lbl_cred.setStyleSheet("" if email else f"color: {_ERROR}; font-weight:bold;")

    def _open_settings(self):
        dlg = SettingsDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._check_credentials()
            self._log("✅ 인증 정보가 저장되었습니다.")

    def _sync_extension(self):
        fmt_map = {0: ".md", 1: ".docx", 2: ".xlsx", 3: ".pdf"}
        ext = fmt_map.get(self.cb_format.currentIndex(), ".md")
        current = self.le_out.text()
        p = Path(current)
        self.le_out.setText(str(p.with_suffix(ext)))

    def _browse(self):
        fmt_map = {
            0: ("Markdown (*.md)", ".md"),
            1: ("Word 문서 (*.docx)", ".docx"),
            2: ("Excel 문서 (*.xlsx)", ".xlsx"),
            3: ("PDF (*.pdf)", ".pdf"),
        }
        filt, ext = fmt_map.get(self.cb_format.currentIndex(), ("All (*)", ""))
        path, _ = QFileDialog.getSaveFileName(
            self, "저장 위치 선택",
            str(Path.home() / f"output{ext}"),
            filt,
        )
        if path:
            self.le_out.setText(path)

    def _start(self):
        url = self.le_url.text().strip()
        if not url:
            QMessageBox.warning(self, "입력 오류", "Confluence 페이지 URL을 입력하세요.")
            return
        if not url.startswith("http"):
            QMessageBox.warning(self, "입력 오류", "올바른 URL 형식이 아닙니다. (http:// 또는 https://로 시작)")
            return

        fmt_map = {0: "md", 1: "docx", 2: "xlsx", 3: "pdf"}
        fmt = fmt_map[self.cb_format.currentIndex()]
        output_path = self.le_out.text().strip()
        include_children = self.chk_children.isChecked()

        self.te_log.clear()
        self.progress_bar.setValue(0)
        self._set_running(True)
        self._log(f"▶ 변환 시작 | 형식: {fmt.upper()} | 하위문서: {'포함' if include_children else '미포함'}")
        self._log(f"   URL: {url}")

        self._worker = ConvertWorker(url, include_children, fmt, output_path)
        self._worker.log.connect(self._log)
        self._worker.progress.connect(self.progress_bar.setValue)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _stop(self):
        if self._worker and self._worker.isRunning():
            self._worker.terminate()
            self._worker.wait()
            self._log("■ 변환이 중단되었습니다.")
            self._set_running(False)

    def _on_finished(self, path: str):
        self._set_running(False)
        self._log(f"\n✅ 변환 완료!  →  {path}")
        self.lbl_status.setText(f"완료: {path}")
        QMessageBox.information(
            self, "완료",
            f"변환이 완료되었습니다.\n\n저장 경로:\n{path}",
        )

    def _on_error(self, msg: str):
        self._set_running(False)
        self._log(f"\n❌ 오류: {msg}")
        self.lbl_status.setText("오류 발생")
        QMessageBox.critical(self, "오류", msg)

    def _set_running(self, running: bool):
        self.btn_run.setEnabled(not running)
        self.btn_stop.setEnabled(running)
        self.le_url.setEnabled(not running)
        self.cb_format.setEnabled(not running)
        self.chk_children.setEnabled(not running)

    def _log(self, msg: str):
        self.te_log.append(msg)
        self.te_log.verticalScrollBar().setValue(
            self.te_log.verticalScrollBar().maximum()
        )
        self.lbl_status.setText(msg[:80])


# ─────────────────────────────────────────────
# 엔트리포인트
# ─────────────────────────────────────────────
def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
