"""View — 인증 설정 다이얼로그.

바인딩:
  View  → ViewModel.save(email, token)  호출
  ViewModel.saved          → accept()
  ViewModel.validation_failed → QMessageBox 표시
"""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QWidget, QLabel, QLineEdit, QMessageBox,
)

from view.theme import ACCENT
from view.widgets import app_icon, make_divider, make_label, make_btn
from viewmodel.settings_viewmodel import SettingsViewModel


class SettingsDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("인증 설정 — Confluence Parser")
        self.setWindowIcon(app_icon())
        self.setMinimumWidth(460)

        self._vm = SettingsViewModel(self)
        self._vm.saved.connect(self.accept)
        self._vm.validation_failed.connect(
            lambda msg: QMessageBox.warning(self, "입력 오류", msg)
        )
        self._build()

    # ── UI 구성 ────────────────────────────────────────
    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(self._make_header())
        root.addWidget(self._make_body())

    def _make_header(self) -> QWidget:
        hdr = QWidget()
        hdr.setStyleSheet(f"background:{ACCENT}; border-radius:0px;")
        layout = QVBoxLayout(hdr)
        layout.setContentsMargins(24, 20, 24, 20)

        title = QLabel("인증 설정")
        title.setStyleSheet(
            "font-size:17px; font-weight:700; color:#fff; background:transparent;"
        )
        sub = QLabel("Confluence 이메일 주소와 API Token을 입력하세요")
        sub.setStyleSheet(
            "font-size:12px; color:rgba(255,255,255,0.75); background:transparent;"
        )
        layout.addWidget(title)
        layout.addWidget(sub)
        return hdr

    def _make_body(self) -> QWidget:
        body = QWidget()
        layout = QVBoxLayout(body)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 24, 24, 20)

        layout.addWidget(make_label("Confluence 이메일"))
        self.le_email = QLineEdit(self._vm.current_email)
        self.le_email.setPlaceholderText("example@company.com")
        layout.addWidget(self.le_email)

        layout.addSpacing(4)
        layout.addWidget(make_label("API Token"))
        self.le_token = QLineEdit(self._vm.current_token)
        self.le_token.setPlaceholderText("토큰을 입력하세요 (기존 값이 있으면 유지)")
        self.le_token.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.le_token)

        hint = QLabel(
            '💡 API Token 발급: '
            f'<a href="https://id.atlassian.com/manage-profile/security/api-tokens" '
            f'style="color:{ACCENT};">Atlassian 보안 설정 열기</a>'
        )
        hint.setOpenExternalLinks(True)
        hint.setObjectName("lbl_sub")
        layout.addWidget(hint)

        layout.addSpacing(8)
        layout.addWidget(make_divider())
        layout.addSpacing(8)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_cancel = make_btn("취소", "btn_secondary", height=36, min_width=88)
        btn_cancel.clicked.connect(self.reject)
        btn_save = make_btn("저장", height=36, min_width=88)
        btn_save.clicked.connect(self._on_save)
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)
        layout.addLayout(btn_row)

        return body

    # ── 이벤트 → ViewModel ────────────────────────────
    def _on_save(self) -> None:
        self._vm.save(self.le_email.text(), self.le_token.text())
