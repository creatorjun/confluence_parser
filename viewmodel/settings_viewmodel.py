# viewmodel/settings_viewmodel.py
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal
from platformdirs import user_config_dir

from domain.ports import ICredentialStore
from infrastructure.constants import APP_NAME, APP_AUTHOR

# 이메일 기본 패턴: RFC 5322 완전 준수 대신 실용적 검증
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _sanitize(value: str) -> str:
    """줄바꿼과 탭을 제거하고 양쪽 공백을 제거.

    .env KEY=VALUE 포맷에서 줄바꿼이 포함되면 파일이 깨진다.
    """
    return value.replace("\r", "").replace("\n", "").replace("\t", " ").strip()


def _validate_email(email: str) -> str | None:
    """유효하면 None, 문제가 있으면 오류 메시지 반환."""
    if not email:
        return "이메일을 입력해 주세요."
    if not _EMAIL_RE.match(email):
        return "이메일 형식이 올바르지 않습니다. (example@company.com)"
    if len(email) > 254:
        return "이메일 주소가 너무 깁니다. (254자 이하)"
    return None


def _validate_token(token: str) -> str | None:
    """유효하면 None, 문제가 있으면 오류 메시지 반환."""
    if not token:
        return "API Token을 입력해 주세요."
    if len(token) < 8:
        return "API Token이 너무 짧습니다. (8자 이상)"
    if len(token) > 2048:
        return "API Token이 너무 깁니다. (2048자 이하)"
    if "\n" in token or "\r" in token:
        return "Token에 줄바꿼이 포함되어 있어 저장할 수 없습니다."
    return None


class SettingsViewModel(QObject):
    saved             = pyqtSignal()
    validation_failed = pyqtSignal(str)

    def __init__(
        self,
        credential_store: ICredentialStore,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._cred_store = credential_store

    # ── 프로퍼티 ───────────────────────────────────────────────────────────────
    @property
    def current_email(self) -> str:
        email, _ = self._cred_store.load()
        return email

    @property
    def current_token(self) -> str:
        _, token = self._cred_store.load()
        return token

    @property
    def config_dir(self) -> str:
        return user_config_dir(APP_NAME, APP_AUTHOR)

    # ── 액션 ───────────────────────────────────────────────────────────────
    def save(self, email: str, token: str) -> None:
        email = _sanitize(email)
        token = _sanitize(token)

        if err := _validate_email(email):
            self.validation_failed.emit(err)
            return

        if err := _validate_token(token):
            self.validation_failed.emit(err)
            return

        self._cred_store.save(email, token)
        self.saved.emit()

    def open_config_folder(self) -> None:
        path = Path(self.config_dir)
        path.mkdir(parents=True, exist_ok=True)
        try:
            if sys.platform == "win32":
                subprocess.Popen(["explorer", str(path)])
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(path)])
            else:
                subprocess.Popen(["xdg-open", str(path)])
        except Exception:
            pass
