# worker.py
"""
QThread 기반 백그라운드 워커
- UI 블로킹 없이 Confluence 수집 + 변환 수행
- 시그널로 진행상황/완료/에러 전달
"""
from __future__ import annotations

from PyQt6.QtCore import QThread, pyqtSignal

from confluence_client import ConfluenceClient
import config


class ConvertWorker(QThread):
    # 시그널 정의
    log      = pyqtSignal(str)   # 진행 로그 한 줄
    progress = pyqtSignal(int)   # 0~100 퍼센트
    finished = pyqtSignal(str)   # 완료 시 출력 파일 경로
    error    = pyqtSignal(str)   # 에러 메시지

    def __init__(
        self,
        page_url: str,
        include_children: bool,
        output_format: str,   # "md" | "docx" | "xlsx" | "pdf"
        output_path: str,
    ):
        super().__init__()
        self.page_url         = page_url
        self.include_children = include_children
        self.output_format    = output_format
        self.output_path      = output_path

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

        # URL 파싱
        self.log.emit(f"URL 파싱 중: {self.page_url}")
        base_url, page_id = client.parse_url(self.page_url)
        self.log.emit(f"Base URL : {base_url}")
        self.log.emit(f"Page ID  : {page_id}")
        self.progress.emit(5)

        # 페이지 수집
        self.log.emit("페이지 수집 중...")
        pages = client.collect_pages(
            base_url, page_id,
            include_children=self.include_children,
            progress_cb=lambda msg: self.log.emit("  " + msg),
        )
        self.log.emit(f"총 {len(pages)}개 페이지 수집 완료")
        self.progress.emit(50)

        # 변환
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

        convert(pages, self.output_path)
        self.progress.emit(100)
        self.log.emit(f"완료: {self.output_path}")
        self.finished.emit(self.output_path)
