# infrastructure/credential_store.py
from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from platformdirs import user_config_dir

from domain.ports import ICredentialStore
from infrastructure.constants import APP_NAME, APP_AUTHOR

_KEYRING_SERVICE  = APP_NAME
_KEYRING_USERNAME = "confluence_api_token"


def _resolve_env_path() -> Path:
    config_dir = Path(user_config_dir(APP_NAME, APP_AUTHOR))
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / ".env"


def _legacy_env_path() -> Path:
    """실행 파일 또는 스크립트 기준 루트 .env 경로 (이전 방식)."""
    if getattr(sys, "frozen", False):
        base = Path(sys.executable).parent
    else:
        base = Path(__file__).parent.parent
    return base / ".env"


_ENV_PATH = _resolve_env_path()


# ── keyring helpers ───────────────────────────────────────────────────────────

def _try_keyring_get() -> str:
    try:
        import keyring
        value = keyring.get_password(_KEYRING_SERVICE, _KEYRING_USERNAME)
        return value or ""
    except Exception:
        return ""


def _try_keyring_set(token: str) -> bool:
    try:
        import keyring
        keyring.set_password(_KEYRING_SERVICE, _KEYRING_USERNAME, token)
        return True
    except Exception:
        return False


# ── migration ─────────────────────────────────────────────────────────────────

def _parse_env_file(path: Path) -> dict[str, str]:
    """단순 KEY=VALUE 파서. 주석·빈 줄 무시."""
    result: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        result[key.strip()] = val.strip()
    return result


def _migrate_legacy_env() -> None:
    """레거시 루트 .env 를 새 경로로 마이그레이션.

    조건:
    - 새 경로 .env 가 아직 없을 것  (이미 마이그레이션 됐거나 신규 설치)
    - 레거시 .env 가 존재할 것
    - CONFLUENCE_EMAIL 또는 CONFLUENCE_API_TOKEN 이 담겨 있을 것

    완료 후 레거시 파일을 .env.migrated 로 이름 변경하여 백업.
    """
    if _ENV_PATH.exists():
        return

    legacy = _legacy_env_path()
    if not legacy.exists():
        return

    try:
        data = _parse_env_file(legacy)
    except OSError:
        return

    email = data.get("CONFLUENCE_EMAIL", "")
    token = data.get("CONFLUENCE_API_TOKEN", "")

    if not email and not token:
        return

    lines: list[str] = []
    if email:
        lines.append(f"CONFLUENCE_EMAIL={email}")
    tmp = _ENV_PATH.with_suffix(".tmp")
    tmp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    tmp.replace(_ENV_PATH)

    if token:
        stored = _try_keyring_set(token)
        if not stored:
            existing = _ENV_PATH.read_text(encoding="utf-8").rstrip()
            _ENV_PATH.write_text(
                existing + f"\nCONFLUENCE_API_TOKEN={token}\n",
                encoding="utf-8",
            )

    migrated_path = legacy.with_name(".env.migrated")
    try:
        legacy.rename(migrated_path)
    except OSError:
        pass


# ── SecureCredentialStore ─────────────────────────────────────────────────────

class SecureCredentialStore(ICredentialStore):
    """이메일은 platformdirs 기반 .env 에, 토큰은 OS 보안 저장소(keyring)에 저장.

    - keyring 사용 불가 환경(headless 서버 등)에서는 .env 에 fallback
    - 첫 실행 시 레거시 루트 .env 를 새 경로로 자동 마이그레이션
    """

    def __init__(self) -> None:
        _migrate_legacy_env()
        load_dotenv(_ENV_PATH, override=True)

    def load(self) -> tuple[str, str]:
        email = os.environ.get("CONFLUENCE_EMAIL", "")
        token = _try_keyring_get()
        if not token:
            token = os.environ.get("CONFLUENCE_API_TOKEN", "")
        return email, token

    def save(self, email: str, token: str) -> None:
        self._save_email_to_env(email)
        stored_in_keyring = _try_keyring_set(token)
        if stored_in_keyring:
            self._remove_token_from_env()
        else:
            self._save_token_to_env(token)
        os.environ["CONFLUENCE_EMAIL"] = email
        os.environ["CONFLUENCE_API_TOKEN"] = token

    # ── private helpers ───────────────────────────────────────────────────────
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
        tmp.replace(_ENV_PATH)
