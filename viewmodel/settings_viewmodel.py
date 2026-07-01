# viewmodel/settings_viewmodel.py
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal
from platformdirs import user_config_dir

from domain.ports import ICredentialStore

_APP_NAME   = "SeculayerDocumentParser"
_APP_AUTHOR = "Seculayer"


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

    # ── 프로퍼티 ──────────────────────────────────────────────────────────
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
        """platformdirs 기반 설정 폴더 경로."""
        return user_config_dir(_APP_NAME, _APP_AUTHOR)

    # ── 액션 ──────────────────────────────────────────────────────────
    def save(self, email: str, token: str) -> None:
        email = email.strip()
        token = token.strip()
        if not email or not token:
            self.validation_failed.emit("이메일과 API Token을 모두 입력해 주세요.")
            return
        self._cred_store.save(email, token)
        self.saved.emit()

    def open_config_folder(self) -> None:
        """OS 기본 파일 탐색기로 설정 폴더를 엽니다."""
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
            pass  # 열기 실패 시 조용히 무시
