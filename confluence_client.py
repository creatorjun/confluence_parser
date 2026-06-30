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
from requests import Response


# ──────────────────────────────────────────────────────────────
# HTTP 에러 변환
# ──────────────────────────────────────────────────────────────
def _friendly_error(resp: Response, page_id: str = "") -> str:
    """HTTP 응답 코드를 사용자 친화적인 메시지로 변환."""
    code = resp.status_code
    target = f" (Page ID: {page_id})" if page_id else ""

    if code == 401:
        return (
            f"[⛔ 401 인증 실패{target}]\n"
            "이메일 또는 API Token이 올바르지 않습니다.\n"
            "⚙ 설정 버튼에서 인증 정보를 다시 입력해 주세요."
        )
    if code == 403:
        return (
            f"[🚫 403 접근 권한 없음{target}]\n"
            "현재 계정은 이 페이지를 볼 수 있는 권한이 없습니다.\n"
            "확인할 사항:\n"
            "  • Confluence 에서 해당 페이지 또는 스페이스의 보기 권한이 있는지 확인\n"
            "  • 비공개 스페이스의 경우 관리자에게 권한 요청 필요"
        )
    if code == 404:
        return (
            f"[🔍 404 페이지를 찾을 수 없음{target}]\n"
            "Page ID가 존재하지 않거나 이미 삭제된 페이지입니다.\n"
            "URL이 올바른지 다시 확인해 주세요."
        )
    if code == 429:
        return (
            f"[⏳ 429 요청 한도 초과{target}]\n"
            "Confluence API 호출 횟수 제한에 걸렸습니다.\n"
            "잠시 후 다시 시도해 주세요."
        )
    if 500 <= code < 600:
        return (
            f"[💥 {code} Confluence 서버 오류{target}]\n"
            "Confluence 서버에서 오류가 발생했습니다.\n"
            "잠시 후 다시 시도하거나 Confluence 상태를 확인해 주세요."
        )
    # 기타
    return (
        f"[HTTP {code} 오류{target}]\n"
        f"{resp.reason}\n"
        f"URL: {resp.url}"
    )


def _raise_for_status(resp: Response, page_id: str = "") -> None:
    """raise_for_status 대체 함수 — 친절한 메시지로 ValueError 리일."""
    if not resp.ok:
        raise PermissionError(_friendly_error(resp, page_id)) if resp.status_code == 403 \
            else RuntimeError(_friendly_error(resp, page_id))


# ──────────────────────────────────────────────────────────────
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
        """
        m = re.search(r"/pages/(\d+)", url)
        if m:
            page_id = m.group(1)
            base = re.match(r"(https?://[^/]+/wiki)", url)
            return (base.group(1) if base else ""), page_id

        m = re.search(r"[?&]pageId=(\d+)", url)
        if m:
            page_id = m.group(1)
            base = re.match(r"(https?://[^/]+/wiki)", url)
            return (base.group(1) if base else ""), page_id

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
        resp = requests.get(
            url, headers=self._headers, auth=self._auth,
            params=params, timeout=30,
        )
        _raise_for_status(resp, page_id)
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
            resp = requests.get(
                url, headers=self._headers, auth=self._auth,
                params=params, timeout=30,
            )
            _raise_for_status(resp, page_id)
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
                    self.collect_pages(
                        base_url, child_id, True, depth + 1, progress_cb
                    )
                )
        return pages
