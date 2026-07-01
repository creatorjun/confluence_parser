# infrastructure/constants.py
"""애플리케이션 공통 상수.

_APP_NAME / _APP_AUTHOR 는 platformdirs 경로 계산과 keyring 서비스명에
공통으로 사용되므로 단일 출처(single source of truth)로 관리한다.
"""
from __future__ import annotations

APP_NAME   = "SeculayerDocumentParser"
APP_AUTHOR = "Seculayer"
