# domain/ports.py
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable

from domain.model import PageNode


class IPageRepository(ABC):
    @abstractmethod
    def collect(
        self,
        url: str,
        include_children: bool,
        progress_cb: Callable[[str], None],
    ) -> list[PageNode]: ...


class IConverter(ABC):
    @abstractmethod
    def convert(self, pages: list[PageNode], output_path: str) -> None: ...


class ICredentialStore(ABC):
    @abstractmethod
    def load(self) -> tuple[str, str]: ...

    @abstractmethod
    def save(self, email: str, token: str) -> None: ...


class IAppSettingsStore(ABC):
    """앱 일반 설정 (자격증명 외) 의 저장/조회 포트."""

    @abstractmethod
    def load(self) -> dict: ...

    @abstractmethod
    def save(self, settings: dict) -> None: ...
