# worker.py
from __future__ import annotations

import re
from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal

from confluence_client import ConfluenceClient
import config


def _safe_filename(name: str) -> str:
    return re.sub(r'[\\/:*?"<>|]', "_", name).strip()


class ConvertWorker(QThread):
    log      = pyqtSignal(str)
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    error    = pyqtSignal(str)

    def __init__(
        self,
        page_url: str,
        include_children: bool,
        output_format: str,
        output_dir: str,
    ):
        super().__init__()
        self.page_url         = page_url
        self.include_children = include_children
        self.output_format    = output_format
        self.output_dir       = output_dir

    def run(self) -> None:
        try:
            self._run()
        except Exception as exc:
            self.error.emit(str(exc))

    def _run(self) -> None:
        email     = config.get("CONFLUENCE_EMAIL")
        api_token = config.get("CONFLUENCE_API_TOKEN")

        if not email or not api_token:
            self.error.emit(
                "이메일과 API 토큰을 먼저 설정하세요.\n"
                "상단 ⚙ 설정 버튼을 눌러 입력해 주세요."
            )
            return

        client = ConfluenceClient(email, api_token)

        self.log.emit(f"URL 파싱 중: {self.page_url}")
        base_url, page_id = client.parse_url(self.page_url)
        self.log.emit(f"Base URL : {base_url}")
        self.log.emit(f"Page ID  : {page_id}")
        self.progress.emit(5)

        self.log.emit("페이지 수집 중...")
        pages = client.collect_pages(
            base_url, page_id,
            include_children=self.include_children,
            progress_cb=lambda msg: self.log.emit("  " + msg),
        )
        self.log.emit(f"총 {len(pages)}개 페이지 수집 완료")
        self.progress.emit(50)

        root_title = pages[0][1] if pages else "output"
        ext_map = {"md": ".md", "docx": ".docx", "xlsx": ".xlsx", "pdf": ".pdf"}
        ext = ext_map.get(self.output_format.lower(), ".md")
        filename = _safe_filename(root_title) + ext
        output_path = str(Path(self.output_dir) / filename)

        self.log.emit(f"{self.output_format.upper()} 변환 중...")
        fmt = self.output_format.lower()
        if fmt == "md":
            from converters.to_md import convert
        elif fmt == "docx":
            from converters.to_docx import convert
        elif fmt in ("xlsx", "excel"):
            from converters.to_excel import convert
        elif fmt == "pdf":
            from converters.to_pdf import convert
        else:
            self.error.emit(f"지원하지 않는 형식: {self.output_format}")
            return

        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        convert(pages, output_path)
        self.progress.emit(100)
        self.log.emit(f"완료: {output_path}")
        self.finished.emit(output_path)
