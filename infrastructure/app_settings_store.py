# infrastructure/app_settings_store.py
from __future__ import annotations

import json
from pathlib import Path

from platformdirs import user_config_dir

from domain.ports import IAppSettingsStore
from infrastructure.constants import APP_NAME, APP_AUTHOR

_DEFAULTS: dict = {
    "fmt_index":        0,      # 0=md, 1=docx, 2=xlsx, 3=pdf
    "include_children": True,
    "output_dir":       "",     # 빈 문자열이면 런타임에 기본 경로 사용
}


def _resolve_settings_path() -> Path:
    config_dir = Path(user_config_dir(APP_NAME, APP_AUTHOR))
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "settings.json"


_SETTINGS_PATH = _resolve_settings_path()


class JsonAppSettingsStore(IAppSettingsStore):
    """앱 일반 설정을 platformdirs 기반 경로의 settings.json 에 저장.

    - 파일이 없으면 기본값 반환
    - 저장은 .tmp → replace() 원자적 교체
    - 알 수 없는 키는 무시, 누락된 키는 기본값으로 보정
    """

    def load(self) -> dict:
        if not _SETTINGS_PATH.exists():
            return dict(_DEFAULTS)
        try:
            raw = json.loads(_SETTINGS_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return dict(_DEFAULTS)
        return {k: raw.get(k, v) for k, v in _DEFAULTS.items()}

    def save(self, settings: dict) -> None:
        clean = {k: settings.get(k, v) for k, v in _DEFAULTS.items()}
        tmp = _SETTINGS_PATH.with_suffix(".tmp")
        tmp.write_text(
            json.dumps(clean, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        tmp.replace(_SETTINGS_PATH)
