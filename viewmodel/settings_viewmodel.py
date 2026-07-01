# viewmodel/settings_viewmodel.py
from __future__ import annotations

from PyQt6.QtCore import QObject, pyqtSignal

from domain.ports import ICredentialStore


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

    @property
    def current_email(self) -> str:
        email, _ = self._cred_store.load()
        return email

    @property
    def current_token(self) -> str:
        _, token = self._cred_store.load()
        return token

    def save(self, email: str, token: str) -> None:
        email = email.strip()
        token = token.strip()
        if not email or not token:
            self.validation_failed.emit("이메일과 API Token을 모두 입력해 주세요.")
            return
        self._cred_store.save(email, token)
        self.saved.emit()
