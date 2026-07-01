# domain/use_cases.py
from __future__ import annotations

import re
from pathlib import Path
from typing import Callable

from domain.model import PageNode
from domain.ports import IConverter, ICredentialStore, IPageRepository


def _safe_filename(name: str) -> str:
    return re.sub(r'[\\/:*?"<>|]', "_", name).strip()


class DownloadUseCase:
    def __init__(
        self,
        repo: IPageRepository,
        converter: IConverter,
        credential_store: ICredentialStore,
        file_extension: str,
    ) -> None:
        self._repo = repo
        self._converter = converter
        self._cred_store = credential_store
        self._ext = file_extension if file_extension.startswith(".") else f".{file_extension}"

    def execute(
        self,
        url: str,
        include_children: bool,
        output_dir: str,
        progress_cb: Callable[[int], None],
        log_cb: Callable[[str], None],
    ) -> str:
        email, token = self._cred_store.load()

        if not email or not token:
            raise ValueError(
                "이메일과 API 토큰을 먼저 설정하세요.\n"
                "상단 ⚙ 설정 버튼을 눌러 입력해 주세요."
            )

        log_cb(f"URL 파싱 중: {url}")
        progress_cb(5)

        log_cb("페이지 수집 중...")
        pages: list[PageNode] = self._repo.collect(
            url,
            include_children,
            progress_cb=lambda msg: log_cb("  " + msg),
        )
        log_cb(f"총 {len(pages)}개 페이지 수집 완료")
        progress_cb(50)

        root_title = pages[0].title if pages else "output"
        filename = _safe_filename(root_title) + self._ext

        Path(output_dir).mkdir(parents=True, exist_ok=True)
        output_path = str(Path(output_dir) / filename)

        log_cb(f"{self._ext.lstrip('.').upper()} 변환 중...")
        self._converter.convert(pages, output_path)
        progress_cb(100)
        log_cb(f"완료: {output_path}")

        return output_path
