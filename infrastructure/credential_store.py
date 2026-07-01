# infrastructure/credential_store.py
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

from domain.ports import ICredentialStore

_ENV_PATH = Path(__file__).parent.parent / ".env"


class EnvCredentialStore(ICredentialStore):
    def __init__(self) -> None:
        load_dotenv(_ENV_PATH, override=True)

    def load(self) -> tuple[str, str]:
        email = os.environ.get("CONFLUENCE_EMAIL", "")
        token = os.environ.get("CONFLUENCE_API_TOKEN", "")
        return email, token

    def save(self, email: str, token: str) -> None:
        lines: list[str] = []
        if _ENV_PATH.exists():
            for line in _ENV_PATH.read_text(encoding="utf-8").splitlines():
                key = line.split("=", 1)[0].strip()
                if key not in ("CONFLUENCE_EMAIL", "CONFLUENCE_API_TOKEN"):
                    lines.append(line)
        lines.append(f"CONFLUENCE_EMAIL={email}")
        lines.append(f"CONFLUENCE_API_TOKEN={token}")
        _ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
        os.environ["CONFLUENCE_EMAIL"] = email
        os.environ["CONFLUENCE_API_TOKEN"] = token
