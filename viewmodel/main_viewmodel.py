# viewmodel/main_viewmodel.py
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal

from application.download_worker import DownloadWorker
from domain.ports import IConverter, ICredentialStore, IPageRepository
from domain.use_cases import DownloadUseCase


class MainViewModel(QObject):
    log_appended        = pyqtSignal(str)
    progress_changed    = pyqtSignal(int)
    convert_finished    = pyqtSignal(str)
    convert_error       = pyqtSignal(str)
    running_changed     = pyqtSignal(bool)
    credentials_changed = pyqtSignal(bool)

    FORMAT_KEYS = ["md", "docx", "xlsx", "pdf"]
    FORMAT_EXT  = {
        "md":   ".md",
        "docx": ".docx",
        "xlsx": ".xlsx",
        "pdf":  ".pdf",
    }

    def __init__(
        self,
        credential_store: ICredentialStore,
        converters: dict[str, IConverter],
        repo: IPageRepository,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._cred_store  = credential_store
        self._converters  = converters
        self._repo        = repo
        self._worker: DownloadWorker | None = None
        self._running     = False

    @property
    def has_credentials(self) -> bool:
        email, token = self._cred_store.load()
        return bool(email and token)

    @property
    def is_running(self) -> bool:
        return self._running

    def default_output_dir(self) -> str:
        return str(Path.home() / "Documents" / "Confluence")

    def extension_for(self, fmt_index: int) -> str:
        return self.FORMAT_EXT.get(self.FORMAT_KEYS[fmt_index], ".md")

    def notify_credentials_updated(self) -> None:
        self.credentials_changed.emit(self.has_credentials)

    def start_convert(
        self,
        url: str,
        include_children: bool,
        fmt_index: int,
        output_dir: str,
    ) -> None:
        if self._running:
            return
        fmt = self.FORMAT_KEYS[fmt_index]
        converter = self._converters[fmt]
        ext = self.FORMAT_EXT[fmt]

        use_case = DownloadUseCase(
            repo=self._repo,
            converter=converter,
            credential_store=self._cred_store,
            file_extension=ext,
        )

        self._set_running(True)
        self.log_appended.emit(
            f"\u25b6 변환 시작 \u2014 형식: {fmt.upper()} \u2022 "
            f"하위문서: {'포함' if include_children else '미포함'}"
        )
        self.log_appended.emit(f"   URL: {url}")

        self._worker = DownloadWorker(use_case, url, include_children, output_dir)
        self._worker.log.connect(self.log_appended)
        self._worker.progress.connect(self.progress_changed)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.error.connect(self._on_worker_error)
        self._worker.start()

    def stop_convert(self) -> None:
        if self._worker and self._worker.isRunning():
            self._worker.terminate()
            self._worker.wait()
            self.log_appended.emit("⏹ 변환이 중단되었습니다.")
            self._set_running(False)

    def _set_running(self, value: bool) -> None:
        self._running = value
        self.running_changed.emit(value)

    def _on_worker_finished(self, path: str) -> None:
        self._set_running(False)
        self.log_appended.emit(f"\n✅ 변환 완료  →  {path}")
        self.convert_finished.emit(path)

    def _on_worker_error(self, msg: str) -> None:
        self._set_running(False)
        self.log_appended.emit(f"\n❌ 오류: {msg}")
        self.convert_error.emit(msg)
