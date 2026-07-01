# infrastructure/credential_store.py
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from platformdirs import user_config_dir

from domain.ports import ICredentialStore

_APP_NAME   = "SeculayerDocumentParser"
_APP_AUTHOR = "Seculayer"
_KEYRING_SERVICE = "SeculayerDocumentParser"
_KEYRING_USERNAME = "confluence_api_token"


def _resolve_env_path() -> Path:
    config_dir = Path(user_config_dir(_APP_NAME, _APP_AUTHOR))
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / ".env"


_ENV_PATH = _resolve_env_path()


def _try_keyring_get() -> str:
    """keyring 사용 가능 환경에서만 토큰을 읽는다. 실패 시 빈 문자열 반환."""
    try:
        import keyring
        value = keyring.get_password(_KEYRING_SERVICE, _KEYRING_USERNAME)
        return value or ""
    except Exception:
        return ""


def _try_keyring_set(token: str) -> bool:
    """keyring 저장 시도. 성공 시 True, 실패 시 False."""
    try:
        import keyring
        keyring.set_password(_KEYRING_SERVICE, _KEYRING_USERNAME, token)
        return True
    except Exception:
        return False


class SecureCredentialStore(ICredentialStore):
    """이메일은 platformdirs 기반 .env 에, 토큰은 OS 보안 저장소(keyring)에 저장.

    keyring 사용 불가 환경(headless 서버 등)에서는 .env 에 fallback.
    """

    def __init__(self) -> None:
        load_dotenv(_ENV_PATH, override=True)

    # ── ICredentialStore ──────────────────────────────
    def load(self) -> tuple[str, str]:
        email = os.environ.get("CONFLUENCE_EMAIL", "")

        # 1순위: OS secure store
        token = _try_keyring_get()
        # 2순위: .env fallback (이전 방식으로 저장된 경우 호환)
        if not token:
            token = os.environ.get("CONFLUENCE_API_TOKEN", "")

        return email, token

    def save(self, email: str, token: str) -> None:
        self._save_email_to_env(email)

        # 토큰 저장: keyring 우선, 실패 시 .env fallback
        stored_in_keyring = _try_keyring_set(token)
        if stored_in_keyring:
            # keyring 에 저장 성공했으면 .env 에서 토큰 제거
            self._remove_token_from_env()
        else:
            # keyring 사용 불가 환경: .env fallback
            self._save_token_to_env(token)

        os.environ["CONFLUENCE_EMAIL"] = email
        os.environ["CONFLUENCE_API_TOKEN"] = token

    # ── private helpers ───────────────────────────────
    def _save_email_to_env(self, email: str) -> None:
        lines = self._read_env_lines(exclude={"CONFLUENCE_EMAIL"})
        lines.append(f"CONFLUENCE_EMAIL={email}")
        self._write_env_lines(lines)

    def _save_token_to_env(self, token: str) -> None:
        lines = self._read_env_lines(exclude={"CONFLUENCE_API_TOKEN"})
        lines.append(f"CONFLUENCE_API_TOKEN={token}")
        self._write_env_lines(lines)

    def _remove_token_from_env(self) -> None:
        lines = self._read_env_lines(exclude={"CONFLUENCE_API_TOKEN"})
        self._write_env_lines(lines)

    def _read_env_lines(self, exclude: set[str] | None = None) -> list[str]:
        exclude = exclude or set()
        if not _ENV_PATH.exists():
            return []
        return [
            line
            for line in _ENV_PATH.read_text(encoding="utf-8").splitlines()
            if line.split("=", 1)[0].strip() not in exclude
        ]

    def _write_env_lines(self, lines: list[str]) -> None:
        tmp = _ENV_PATH.with_suffix(".tmp")
        tmp.write_text("\n".join(lines) + "\n", encoding="utf-8")
        tmp.replace(_ENV_PATH)  # 원자적 교체 — 저장 중 비정상 종료 대비
