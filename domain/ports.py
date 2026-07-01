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
