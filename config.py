# config.py
"""
설정 로더 - .env 파일 우선, 없으면 환경변수 폴백
"""
from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

_ENV_PATH = Path(__file__).parent / ".env"
load_dotenv(_ENV_PATH, override=True)


def get(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


def save(email: str, token: str) -> None:
    """이메일과 API 토큰을 .env 파일에 저장"""
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


EMAIL: str = get("CONFLUENCE_EMAIL")
API_TOKEN: str = get("CONFLUENCE_API_TOKEN")
