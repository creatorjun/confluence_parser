# confluence_client.py
"""
Confluence REST API 클라이언트
- URL에서 page_id 추출
- 페이지 HTML 본문 조회
- 하위 페이지 재귀 수집
"""
from __future__ import annotations

import re
from typing import Callable

import requests
from requests.auth import HTTPBasicAuth


class ConfluenceClient:
    def __init__(self, email: str, token: str):
        self._auth = HTTPBasicAuth(email, token)
        self._headers = {"Accept": "application/json"}

    # ------------------------------------------------------------------ #
    # URL 파싱
    # ------------------------------------------------------------------ #
    @staticmethod
    def parse_url(url: str) -> tuple[str, str]:
        """
        Confluence 페이지 URL에서 (base_url, page_id) 반환.
        지원 형식:
          - .../wiki/spaces/SPACE/pages/123456/title
          - .../wiki/pages/viewpage.action?pageId=123456
          - .../wiki/display/SPACE/title (제목 기반 - 추가 API 조회 필요)
        """
        # 숫자 page_id 포함 경로
        m = re.search(r"/pages/(\d+)", url)
        if m:
            page_id = m.group(1)
            base = re.match(r"(https?://[^/]+/wiki)", url)
            base_url = base.group(1) if base else ""
            return base_url, page_id

        # ?pageId=xxx
        m = re.search(r"[?&]pageId=(\d+)", url)
        if m:
            page_id = m.group(1)
            base = re.match(r"(https?://[^/]+/wiki)", url)
            base_url = base.group(1) if base else ""
            return base_url, page_id

        raise ValueError(
            "URL에서 page_id를 찾을 수 없습니다.\n"
            "지원 형식:\n"
            "  .../wiki/spaces/SPACE/pages/123456/...\n"
            "  .../wiki/pages/viewpage.action?pageId=123456"
        )

    # ------------------------------------------------------------------ #
    # 단일 페이지
    # ------------------------------------------------------------------ #
    def get_page(self, base_url: str, page_id: str) -> tuple[str, str]:
        url = f"{base_url}/rest/api/content/{page_id}"
        params = {"expand": "body.export_view,title"}
        resp = requests.get(url, headers=self._headers, auth=self._auth, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data["title"], data["body"]["export_view"]["value"]

    # ------------------------------------------------------------------ #
    # 하위 페이지 ID 목록
    # ------------------------------------------------------------------ #
    def get_children(self, base_url: str, page_id: str) -> list[str]:
        ids: list[str] = []
        start, limit = 0, 50
        while True:
            url = f"{base_url}/rest/api/content/{page_id}/child/page"
            params = {"limit": limit, "start": start, "expand": ""}
            resp = requests.get(url, headers=self._headers, auth=self._auth, params=params, timeout=30)
            resp.raise_for_status()
            results = resp.json().get("results", [])
            ids.extend(r["id"] for r in results)
            if len(results) < limit:
                break
            start += limit
        return ids

    # ------------------------------------------------------------------ #
    # 재귀 수집
    # ------------------------------------------------------------------ #
    def collect_pages(
        self,
        base_url: str,
        page_id: str,
        include_children: bool = True,
        depth: int = 0,
        progress_cb: Callable[[str], None] | None = None,
    ) -> list[tuple[int, str, str]]:
        pages: list[tuple[int, str, str]] = []
        title, html_body = self.get_page(base_url, page_id)
        if progress_cb:
            progress_cb(f"[{depth}] {title}")
        pages.append((depth, title, html_body))
        if include_children:
            for child_id in self.get_children(base_url, page_id):
                pages.extend(
                    self.collect_pages(base_url, child_id, True, depth + 1, progress_cb)
                )
        return pages
