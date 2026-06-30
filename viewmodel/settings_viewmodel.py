"""ViewModel — 인증 설정 저장/조회."""
from __future__ import annotations

from PyQt6.QtCore import QObject, pyqtSignal

import config


class SettingsViewModel(QObject):
    saved = pyqtSignal()          # 저장 성공
    validation_failed = pyqtSignal(str)  # 유효성 실패 메시지

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)

    @property
    def current_email(self) -> str:
        return config.get("CONFLUENCE_EMAIL") or ""

    @property
    def current_token(self) -> str:
        return config.get("CONFLUENCE_API_TOKEN") or ""

    def save(self, email: str, token: str) -> None:
        email = email.strip()
        token = token.strip()
        if not email or not token:
            self.validation_failed.emit("이메일과 API Token을 모두 입력해 주세요.")
            return
        config.save(email, token)
        self.saved.emit()
