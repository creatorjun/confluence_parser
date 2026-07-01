# application/download_worker.py
from __future__ import annotations

from PyQt6.QtCore import QThread, pyqtSignal

from domain.use_cases import DownloadUseCase


class DownloadWorker(QThread):
    log      = pyqtSignal(str)
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    error    = pyqtSignal(str)

    def __init__(
        self,
        use_case: DownloadUseCase,
        url: str,
        include_children: bool,
        output_dir: str,
    ) -> None:
        super().__init__()
        self._use_case        = use_case
        self._url             = url
        self._include_children = include_children
        self._output_dir      = output_dir

    def run(self) -> None:
        try:
            path = self._use_case.execute(
                url=self._url,
                include_children=self._include_children,
                output_dir=self._output_dir,
                progress_cb=lambda p: self.progress.emit(p),
                log_cb=lambda m: self.log.emit(m),
            )
            self.finished.emit(path)
        except Exception as exc:
            self.error.emit(str(exc))
