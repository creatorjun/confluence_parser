# gui.py
"""
Confluence Parser — PyQt6 GUI (Light Theme)

아키텍처:
  gui.py               ← View   (PyQt6 메인 윈도우 + 설정 다이얼로그)
  worker.py            ← Worker (QThread 백그라운드 변환)
  confluence_client.py ← Model  (REST API + URL 파싱)
  converters/          ← 각 포맷 변환기
  html_cleaner.py      ← HTML 정제
  config.py            ← .env 로더/저장
"""
from __future__ import annotations

import sys
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QCheckBox,
    QComboBox, QTextEdit, QProgressBar,
    QFileDialog, QDialog,
    QMessageBox, QFrame, QGroupBox, QSizePolicy, QSpacerItem,
)

import config
from worker import ConvertWorker

# ─────────────────────────────────────────────
# 라이트 테마 팔레트
# ─────────────────────────────────────────────
_BG         = "#F7F8FA"
_SURFACE    = "#FFFFFF"
_SURFACE2   = "#F0F2F5"
_BORDER     = "#DDE1E7"
_BORDER_FOC = "#2563EB"
_ACCENT     = "#2563EB"
_ACCENT_H   = "#1D4ED8"
_ACCENT_P   = "#1E40AF"
_ACCENT_DIS = "#93C5FD"
_TEXT       = "#111827"
_TEXT_SEC   = "#6B7280"
_TEXT_HINT  = "#9CA3AF"
_SUCCESS    = "#059669"
_ERROR      = "#DC2626"
_WARN       = "#D97706"
_LOG_BG     = "#FAFBFC"
_HDR_BG     = "#FFFFFF"
_STATUS_BG  = "#F0F2F5"

_QSS = f"""
/* 다이얼로그 포함 전체 배경 */
QWidget {{
    background: {_BG};
    color: {_TEXT};
    font-family: 'Malgun Gothic', 'Segoe UI', 'Apple SD Gothic Neo', sans-serif;
    font-size: 13px;
}}

/* 헤더 패널 */
QWidget#header_panel {{
    background: {_HDR_BG};
    border-bottom: 1px solid {_BORDER};
}}

/* 온화된 그룹박스 */
QGroupBox {{
    background: {_SURFACE};
    border: 1px solid {_BORDER};
    border-radius: 10px;
    margin-top: 10px;
    padding: 14px 14px 12px 14px;
    font-weight: 600;
    font-size: 13px;
    color: {_TEXT};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 14px;
    padding: 0 6px;
    background: {_SURFACE};
    color: {_TEXT_SEC};
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}}

/* 입력 필드 */
QLineEdit {{
    background: {_SURFACE};
    border: 1.5px solid {_BORDER};
    border-radius: 7px;
    padding: 9px 12px;
    color: {_TEXT};
    font-size: 13px;
    selection-background-color: {_ACCENT};
    selection-color: #fff;
}}
QLineEdit:hover {{ border-color: #B0B8C8; }}
QLineEdit:focus {{
    border-color: {_BORDER_FOC};
    background: {_SURFACE};
}}
QLineEdit:disabled {{
    background: {_SURFACE2};
    color: {_TEXT_HINT};
}}

/* 콤보박스 */
QComboBox {{
    background: {_SURFACE};
    border: 1.5px solid {_BORDER};
    border-radius: 7px;
    padding: 9px 36px 9px 12px;
    color: {_TEXT};
    font-size: 13px;
    min-width: 140px;
}}
QComboBox:hover {{ border-color: #B0B8C8; }}
QComboBox:focus {{ border-color: {_BORDER_FOC}; }}
QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 30px;
    border-left: 1px solid {_BORDER};
    border-top-right-radius: 7px;
    border-bottom-right-radius: 7px;
    background: {_SURFACE2};
}}
QComboBox::down-arrow {{
    width: 0; height: 0;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {_TEXT_SEC};
    margin-top: 2px;
}}
QComboBox QAbstractItemView {{
    background: {_SURFACE};
    border: 1px solid {_BORDER};
    border-radius: 6px;
    outline: none;
    color: {_TEXT};
    selection-background-color: #EFF6FF;
    selection-color: {_ACCENT};
    padding: 4px;
}}
QComboBox:disabled {{
    background: {_SURFACE2};
    color: {_TEXT_HINT};
}}

/* 기본 버튼 (액센트 Primary) */
QPushButton {{
    background: {_ACCENT};
    color: #ffffff;
    border: none;
    border-radius: 7px;
    padding: 9px 20px;
    font-weight: 600;
    font-size: 13px;
    letter-spacing: 0.2px;
}}
QPushButton:hover   {{ background: {_ACCENT_H}; }}
QPushButton:pressed {{ background: {_ACCENT_P}; }}
QPushButton:disabled {{
    background: {_ACCENT_DIS};
    color: #fff;
}}

/* Secondary 버튼 */
QPushButton#btn_secondary {{
    background: {_SURFACE};
    color: {_TEXT};
    border: 1.5px solid {_BORDER};
    font-weight: 500;
}}
QPushButton#btn_secondary:hover {{
    background: {_SURFACE2};
    border-color: {_BORDER_FOC};
    color: {_ACCENT};
}}
QPushButton#btn_secondary:pressed {{
    background: #E0EAFE;
}}
QPushButton#btn_secondary:disabled {{
    background: {_SURFACE2};
    color: {_TEXT_HINT};
    border-color: {_BORDER};
}}

/* Secondary 버튼 — 경고(인증 미설정) 상태 */
QPushButton#btn_settings_warn {{
    background: {_SURFACE};
    color: {_ERROR};
    border: 1.5px solid {_ERROR};
    font-weight: 700;
    border-radius: 7px;
    padding: 9px 20px;
    font-size: 13px;
}}
QPushButton#btn_settings_warn:hover {{
    background: #FEE2E2;
    border-color: #B91C1C;
    color: #B91C1C;
}}
QPushButton#btn_settings_warn:pressed {{
    background: #FECACA;
}}

/* Danger 버튼 */
QPushButton#btn_danger {{
    background: #EF4444;
    color: #ffffff;
    border: none;
}}
QPushButton#btn_danger:hover   {{ background: #DC2626; }}
QPushButton#btn_danger:pressed {{ background: #B91C1C; }}
QPushButton#btn_danger:disabled {{
    background: #FCA5A5;
    color: #fff;
}}

/* 체크박스 */
QCheckBox {{
    spacing: 8px;
    color: {_TEXT};
    background: transparent;
    font-size: 13px;
}}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 2px solid {_BORDER};
    border-radius: 4px;
    background: {_SURFACE};
}}
QCheckBox::indicator:hover  {{ border-color: {_BORDER_FOC}; }}
QCheckBox::indicator:checked {{
    background: {_ACCENT};
    border-color: {_ACCENT};
    image: none;
}}
QCheckBox:disabled {{ color: {_TEXT_HINT}; }}

/* 로그 뇸 */
QTextEdit {{
    background: {_LOG_BG};
    border: 1.5px solid {_BORDER};
    border-radius: 7px;
    padding: 8px 10px;
    color: {_TEXT};
    font-family: 'Consolas', 'D2Coding', 'Courier New', monospace;
    font-size: 12px;
    line-height: 1.6;
}}

/* 진행률바 */
QProgressBar {{
    background: {_SURFACE2};
    border: none;
    border-radius: 5px;
    height: 8px;
    text-align: center;
    color: transparent;
}}
QProgressBar::chunk {{
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 {_ACCENT}, stop:1 #60A5FA
    );
    border-radius: 5px;
}}

/* 상태바 */
QStatusBar {{
    background: {_STATUS_BG};
    border-top: 1px solid {_BORDER};
    color: {_TEXT_SEC};
    font-size: 12px;
    padding: 2px 8px;
}}

/* 타이틀 레이블 */
QLabel#lbl_title {{
    font-size: 20px;
    font-weight: 700;
    color: {_TEXT};
    background: transparent;
    letter-spacing: -0.3px;
}}
QLabel#lbl_title_accent {{
    font-size: 20px;
    font-weight: 700;
    color: {_ACCENT};
    background: transparent;
    letter-spacing: -0.3px;
}}
QLabel#lbl_sub {{
    font-size: 12px;
    color: {_TEXT_SEC};
    background: transparent;
}}

/* 구분선 */
QFrame#divider {{
    background: {_BORDER};
    border: none;
    max-height: 1px;
    min-height: 1px;
}}

/* 스크롤바 */
QScrollBar:vertical {{
    background: {_BG};
    width: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: {_BORDER};
    border-radius: 4px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{ background: #B0B8C8; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}

/* 다이얼로그 */
QDialog {{
    background: {_SURFACE};
}}
"""


# ─────────────────────────────────────────────
# 아이콘 헬퍼
# ─────────────────────────────────────────────
_ICO_PATH = Path(__file__).parent / "icon" / "parser.ico"


def _app_icon() -> QIcon:
    if _ICO_PATH.exists():
        return QIcon(str(_ICO_PATH))
    from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont as QF
    pm = QPixmap(64, 64)
    pm.fill(QColor(_ACCENT))
    p = QPainter(pm)
    p.setPen(QColor("#ffffff"))
    f = QF(); f.setBold(True); f.setPixelSize(30)
    p.setFont(f)
    p.drawText(pm.rect(), Qt.AlignmentFlag.AlignCenter, "CP")
    p.end()
    return QIcon(pm)


# ─────────────────────────────────────────────
# 세퍼레이터 / 레이블 헬퍼
# ─────────────────────────────────────────────
def _divider() -> QFrame:
    f = QFrame()
    f.setObjectName("divider")
    f.setFrameShape(QFrame.Shape.HLine)
    f.setFixedHeight(1)
    return f


def _label(text: str, obj_name: str = "", color: str = "") -> QLabel:
    lbl = QLabel(text)
    if obj_name:
        lbl.setObjectName(obj_name)
    if color:
        lbl.setStyleSheet(f"color:{color}; background:transparent;")
    return lbl


def _btn(text: str, obj_name: str = "", height: int = 36,
         min_width: int = 0) -> QPushButton:
    """텍스트 잘림 없는 버튼 헬퍼.
    - setFixedSize 대신 setFixedHeight + setMinimumWidth 사용
    - QSS padding 이 나머지 너비를 자동 확장
    """
    btn = QPushButton(text)
    if obj_name:
        btn.setObjectName(obj_name)
    btn.setFixedHeight(height)
    if min_width:
        btn.setMinimumWidth(min_width)
    return btn


# ─────────────────────────────────────────────
# 설정 다이얼로그
# ─────────────────────────────────────────────
class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("인증 설정 — Confluence Parser")
        self.setWindowIcon(_app_icon())
        self.setMinimumWidth(460)
        self.setStyleSheet(_QSS)
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        # 타이틀 헤더
        hdr = QWidget()
        hdr.setStyleSheet(f"background:{_ACCENT}; border-radius:0px;")
        hdr_layout = QVBoxLayout(hdr)
        hdr_layout.setContentsMargins(24, 20, 24, 20)
        t = QLabel("인증 설정")
        t.setStyleSheet("font-size:17px; font-weight:700; color:#fff; background:transparent;")
        sub = QLabel("Confluence 이메일 주소와 API Token을 입력하세요")
        sub.setStyleSheet("font-size:12px; color:rgba(255,255,255,0.75); background:transparent;")
        hdr_layout.addWidget(t)
        hdr_layout.addWidget(sub)
        root.addWidget(hdr)

        # 본문
        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setSpacing(12)
        body_layout.setContentsMargins(24, 24, 24, 20)

        body_layout.addWidget(_label("Confluence 이메일"))
        self.le_email = QLineEdit(config.get("CONFLUENCE_EMAIL"))
        self.le_email.setPlaceholderText("example@company.com")
        body_layout.addWidget(self.le_email)

        body_layout.addSpacing(4)
        body_layout.addWidget(_label("API Token"))
        self.le_token = QLineEdit(config.get("CONFLUENCE_API_TOKEN"))
        self.le_token.setPlaceholderText("토큰을 입력하세요 (기존 값이 있으면 유지)")
        self.le_token.setEchoMode(QLineEdit.EchoMode.Password)
        body_layout.addWidget(self.le_token)

        hint = QLabel(
            '💡 API Token 발급: '
            '<a href="https://id.atlassian.com/manage-profile/security/api-tokens" '
            f'style="color:{_ACCENT};">Atlassian 보안 설정 열기</a>'
        )
        hint.setOpenExternalLinks(True)
        hint.setObjectName("lbl_sub")
        body_layout.addWidget(hint)

        body_layout.addSpacing(8)
        body_layout.addWidget(_divider())
        body_layout.addSpacing(8)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_cancel = _btn("취소", "btn_secondary", height=36, min_width=88)
        btn_cancel.clicked.connect(self.reject)
        btn_save = _btn("저장", height=36, min_width=88)
        btn_save.clicked.connect(self._save)
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)
        body_layout.addLayout(btn_row)

        root.addWidget(body)

    def _save(self):
        email = self.le_email.text().strip()
        token = self.le_token.text().strip()
        if not email or not token:
            QMessageBox.warning(self, "입력 오류",
                                "이메일과 API Token을 모두 입력해 주세요.")
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
        self.setWindowIcon(_app_icon())
        self.setMinimumSize(800, 640)
        self.resize(940, 720)
        self.setStyleSheet(_QSS)
        self._worker: ConvertWorker | None = None
        self._build_ui()
        self._check_credentials()

    # ── UI 구성 ─────────────────────────────
    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ── 헤더 패널 ──
        hdr_panel = QWidget()
        hdr_panel.setObjectName("header_panel")
        hdr_panel.setFixedHeight(64)
        hdr_panel.setStyleSheet(
            f"background:{_HDR_BG}; border-bottom:1px solid {_BORDER};"
        )
        hdr_layout = QHBoxLayout(hdr_panel)
        hdr_layout.setContentsMargins(24, 0, 20, 0)
        hdr_layout.setSpacing(6)

        # 로고
        logo_row = QHBoxLayout()
        logo_row.setSpacing(4)
        lbl_logo1 = QLabel("Confluence")
        lbl_logo1.setObjectName("lbl_title")
        lbl_logo2 = QLabel("Parser")
        lbl_logo2.setObjectName("lbl_title_accent")
        logo_row.addWidget(lbl_logo1)
        logo_row.addWidget(lbl_logo2)
        hdr_layout.addLayout(logo_row)
        hdr_layout.addStretch()

        # 설정 버튼 — 너비를 텍스트에 맞게 자동 확장
        self.btn_settings = _btn("⚙  설정", "btn_secondary", height=36, min_width=90)
        self.btn_settings.clicked.connect(self._open_settings)
        hdr_layout.addWidget(self.btn_settings)

        root_layout.addWidget(hdr_panel)

        # ── 콘텐츠 영역 ──
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(28, 20, 28, 16)
        content_layout.setSpacing(16)
        root_layout.addWidget(content)

        # ── URL + 옵션 그룹 ──
        grp_input = QGroupBox("변환 설정")
        grid = QGridLayout(grp_input)
        grid.setSpacing(10)
        grid.setContentsMargins(14, 20, 14, 14)
        grid.setColumnStretch(1, 1)

        lbl_url = _label("Confluence 페이지 URL", color=_TEXT_SEC)
        lbl_url.setStyleSheet(f"font-size:11px; font-weight:600; color:{_TEXT_SEC};"
                               "text-transform:uppercase; background:transparent;")
        grid.addWidget(lbl_url, 0, 0, 1, 5)

        self.le_url = QLineEdit()
        self.le_url.setPlaceholderText(
            "https://your-instance.atlassian.net/wiki/spaces/SPACE/pages/123456/page-title"
        )
        self.le_url.setFixedHeight(40)
        grid.addWidget(self.le_url, 1, 0, 1, 5)

        lbl_fmt = _label("출력 형식", color=_TEXT_SEC)
        lbl_fmt.setStyleSheet(f"font-size:11px; font-weight:600; color:{_TEXT_SEC};"
                               "text-transform:uppercase; background:transparent;")
        grid.addWidget(lbl_fmt, 2, 0)

        self.cb_format = QComboBox()
        self.cb_format.addItems([
            "Markdown (.md)",
            "Word (.docx)",
            "Excel (.xlsx)",
            "PDF (.pdf)",
        ])
        self.cb_format.setFixedHeight(40)
        self.cb_format.setFixedWidth(200)
        grid.addWidget(self.cb_format, 2, 1)

        self.chk_children = QCheckBox("하위 문서 포함")
        self.chk_children.setChecked(True)
        grid.addWidget(self.chk_children, 2, 2)

        grid.addItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum),
            2, 3,
        )

        lbl_out = _label("저장 경로", color=_TEXT_SEC)
        lbl_out.setStyleSheet(f"font-size:11px; font-weight:600; color:{_TEXT_SEC};"
                               "text-transform:uppercase; background:transparent;")
        grid.addWidget(lbl_out, 3, 0)

        self.le_out = QLineEdit(str(Path.home() / "output.md"))
        self.le_out.setFixedHeight(40)
        grid.addWidget(self.le_out, 3, 1, 1, 3)

        # ✅ 찾기 버튼: setFixedSize 제거 → 하이 + minWidth
        btn_browse = _btn("📂  찾기", "btn_secondary", height=40, min_width=88)
        btn_browse.clicked.connect(self._browse)
        grid.addWidget(btn_browse, 3, 4)

        self.cb_format.currentIndexChanged.connect(self._sync_extension)
        content_layout.addWidget(grp_input)

        # ── 실행 버튼 행 ──
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        btn_row.addStretch()

        self.btn_run = _btn("▶  변환 시작", height=44, min_width=148)
        self.btn_run.clicked.connect(self._start)
        btn_row.addWidget(self.btn_run)

        self.btn_stop = _btn("⏹  중단", "btn_danger", height=44, min_width=100)
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self._stop)
        btn_row.addWidget(self.btn_stop)

        content_layout.addLayout(btn_row)

        # ── 진행률바 ──
        prog_wrapper = QWidget()
        prog_wrapper.setStyleSheet("background:transparent;")
        prog_layout = QVBoxLayout(prog_wrapper)
        prog_layout.setContentsMargins(0, 0, 0, 0)
        prog_layout.setSpacing(4)

        prog_hdr = QHBoxLayout()
        lbl_prog = _label("진행 상태", color=_TEXT_SEC)
        lbl_prog.setStyleSheet(f"font-size:11px; font-weight:600; color:{_TEXT_SEC};"
                                "text-transform:uppercase; background:transparent;")
        prog_hdr.addWidget(lbl_prog)
        prog_hdr.addStretch()
        self.lbl_pct = _label("0%", color=_TEXT_SEC)
        self.lbl_pct.setStyleSheet(f"font-size:11px; color:{_TEXT_SEC}; background:transparent;")
        prog_hdr.addWidget(self.lbl_pct)
        prog_layout.addLayout(prog_hdr)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(8)
        prog_layout.addWidget(self.progress_bar)
        content_layout.addWidget(prog_wrapper)

        # ── 로그 그룹 ──
        grp_log = QGroupBox("진행 로그")
        log_layout = QVBoxLayout(grp_log)
        log_layout.setContentsMargins(12, 16, 12, 12)
        log_layout.setSpacing(8)

        self.te_log = QTextEdit()
        self.te_log.setReadOnly(True)
        self.te_log.setMinimumHeight(190)
        log_layout.addWidget(self.te_log)

        log_foot = QHBoxLayout()
        log_foot.addStretch()
        # ✅ 로그 지우기 버튼: setFixedSize 제거 → 하이 + minWidth
        btn_clear = _btn("로그 지우기", "btn_secondary", height=34, min_width=100)
        btn_clear.clicked.connect(self.te_log.clear)
        log_foot.addWidget(btn_clear)
        log_layout.addLayout(log_foot)

        content_layout.addWidget(grp_log)

        # ── 상태바 ──
        self.lbl_status = QLabel("대기 중…")
        self.statusBar().addWidget(self.lbl_status)

    # ── 슬롯 ────────────────────────────────
    def _check_credentials(self):
        """인증 정보 유무에 따라 설정 버튼 스타일을 전환한다."""
        has_cred = bool(config.get("CONFLUENCE_EMAIL") and config.get("CONFLUENCE_API_TOKEN"))
        if has_cred:
            self.btn_settings.setText("⚙  설정")
            self.btn_settings.setObjectName("btn_secondary")
        else:
            self.btn_settings.setText("❗ 설정 필요")
            self.btn_settings.setObjectName("btn_settings_warn")
        self.btn_settings.setStyle(self.btn_settings.style())

    def _open_settings(self):
        dlg = SettingsDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._check_credentials()
            self._log("✅ 인증 정보가 저장되었습니다.")

    def _sync_extension(self):
        ext_map = {0: ".md", 1: ".docx", 2: ".xlsx", 3: ".pdf"}
        ext = ext_map.get(self.cb_format.currentIndex(), ".md")
        self.le_out.setText(str(Path(self.le_out.text()).with_suffix(ext)))

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
            str(Path.home() / f"output{ext}"), filt,
        )
        if path:
            self.le_out.setText(path)

    def _start(self):
        url = self.le_url.text().strip()
        if not url:
            QMessageBox.warning(self, "입력 오류",
                                "Confluence 페이지 URL을 입력하세요.")
            return
        if not url.startswith("http"):
            QMessageBox.warning(self, "입력 오류",
                                "URL은 http:// 또는 https://로 시작해야 합니다.")
            return

        fmt_map = {0: "md", 1: "docx", 2: "xlsx", 3: "pdf"}
        fmt = fmt_map[self.cb_format.currentIndex()]
        output_path = self.le_out.text().strip()
        include_children = self.chk_children.isChecked()

        self.te_log.clear()
        self._set_progress(0)
        self._set_running(True)
        self._log(f"▶ 변환 시작 — 형식: {fmt.upper()} • "
                  f"하위문서: {'포함' if include_children else '미포함'}")
        self._log(f"   URL: {url}")

        self._worker = ConvertWorker(url, include_children, fmt, output_path)
        self._worker.log.connect(self._log)
        self._worker.progress.connect(self._set_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _stop(self):
        if self._worker and self._worker.isRunning():
            self._worker.terminate()
            self._worker.wait()
            self._log("⏹ 변환이 중단되었습니다.")
            self._set_running(False)

    def _on_finished(self, path: str):
        self._set_running(False)
        self._log(f"\n✅ 변환 완료  →  {path}")
        self.lbl_status.setText(f"완료: {Path(path).name}")
        QMessageBox.information(
            self, "변환 완료",
            f"성공적으로 변환되었습니다.\n\n저장 경로:\n{path}",
        )

    def _on_error(self, msg: str):
        self._set_running(False)
        self._log(f"\n❌ 오류: {msg}")
        self.lbl_status.setText("오류 발생")
        QMessageBox.critical(self, "오류 발생", msg)

    def _set_running(self, running: bool):
        self.btn_run.setEnabled(not running)
        self.btn_stop.setEnabled(running)
        self.le_url.setEnabled(not running)
        self.cb_format.setEnabled(not running)
        self.chk_children.setEnabled(not running)

    def _set_progress(self, value: int):
        self.progress_bar.setValue(value)
        self.lbl_pct.setText(f"{value}%")

    def _log(self, msg: str):
        self.te_log.append(msg)
        sb = self.te_log.verticalScrollBar()
        sb.setValue(sb.maximum())
        self.lbl_status.setText(msg[:90])


# ─────────────────────────────────────────────
# 엔트리포인트
# ─────────────────────────────────────────────
def main():
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "com.confluence.parser.gui"
        )
    except Exception:
        pass

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName("Confluence Downloader")
    app.setOrganizationName("Seculayer")
    app.setWindowIcon(_app_icon())

    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
