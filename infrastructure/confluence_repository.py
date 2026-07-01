# infrastructure/confluence_repository.py
from __future__ import annotations

import re
from typing import Callable

import requests
from requests import Response
from requests.auth import HTTPBasicAuth

from domain.model import PageNode
from domain.ports import IPageRepository


def _friendly_error(resp: Response, page_id: str = "") -> str:
    code = resp.status_code
    target = f" (Page ID: {page_id})" if page_id else ""

    if code == 401:
        return (
            f"[\u26d4 401 \uc778\uc99d \uc2e4\ud328{target}]\n"
            "\uc774\uba54\uc77c \ub610\ub294 API Token\uc774 \uc62c\ubc14\ub974\uc9c0 \uc54a\uc2b5\ub2c8\ub2e4.\n"
            "\u2699 \uc124\uc815 \ubc84\ud2bc\uc5d0\uc11c \uc778\uc99d \uc815\ubcf4\ub97c \ub2e4\uc2dc \uc785\ub825\ud574 \uc8fc\uc138\uc694."
        )
    if code == 403:
        return (
            f"[\U0001f6ab 403 \uc811\uadfc \uad8c\ud55c \uc5c6\uc74c{target}]\n"
            "\ud604\uc7ac \uacc4\uc815\uc740 \uc774 \ud398\uc774\uc9c0\ub97c \ubcfc \uc218 \uc788\ub294 \uad8c\ud55c\uc774 \uc5c6\uc2b5\ub2c8\ub2e4.\n"
            "\ud655\uc778\ud560 \uc0ac\ud56d:\n"
            "  \u2022 Confluence \uc5d0\uc11c \ud574\ub2f9 \ud398\uc774\uc9c0 \ub610\ub294 \uc2a4\ud398\uc774\uc2a4\uc758 \ubcf4\uae30 \uad8c\ud55c\uc774 \uc788\ub294\uc9c0 \ud655\uc778\n"
            "  \u2022 \ube44\uacf5\uac1c \uc2a4\ud398\uc774\uc2a4\uc758 \uacbd\uc6b0 \uad00\ub9ac\uc790\uc5d0\uac8c \uad8c\ud55c \uc694\uccad \ud544\uc694"
        )
    if code == 404:
        return (
            f"[\U0001f50d 404 \ud398\uc774\uc9c0\ub97c \ucc3e\uc744 \uc218 \uc5c6\uc74c{target}]\n"
            "Page ID\uac00 \uc874\uc7ac\ud558\uc9c0 \uc54a\uac70\ub098 \uc774\ubbf8 \uc0ad\uc81c\ub41c \ud398\uc774\uc9c0\uc785\ub2c8\ub2e4.\n"
            "URL\uc774 \uc62c\ubc14\ub978\uc9c0 \ub2e4\uc2dc \ud655\uc778\ud574 \uc8fc\uc138\uc694."
        )
    if code == 429:
        return (
            f"[\u23f3 429 \uc694\uccad \ud55c\ub3c4 \ucd08\uacfc{target}]\n"
            "Confluence API \ud638\ucd9c \ud69f\uc218 \uc81c\ud55c\uc5d0 \uac78\ub838\uc2b5\ub2c8\ub2e4.\n"
            "\uc78a\uc2dc \ud6c4 \ub2e4\uc2dc \uc2dc\ub3c4\ud574 \uc8fc\uc138\uc694."
        )
    if 500 <= code < 600:
        return (
            f"[\U0001f4a5 {code} Confluence \uc11c\ubc84 \uc624\ub958{target}]\n"
            "Confluence \uc11c\ubc84\uc5d0\uc11c \uc624\ub958\uac00 \ubc1c\uc0dd\ud588\uc2b5\ub2c8\ub2e4.\n"
            "\uc78a\uc2dc \ud6c4 \ub2e4\uc2dc \uc2dc\ub3c4\ud558\uac70\ub098 Confluence \uc0c1\ud0dc\ub97c \ud655\uc778\ud574 \uc8fc\uc138\uc694."
        )
    return (
        f"[HTTP {code} \uc624\ub958{target}]\n"
        f"{resp.reason}\n"
        f"URL: {resp.url}"
    )


def _raise_for_status(resp: Response, page_id: str = "") -> None:
    if not resp.ok:
        if resp.status_code == 403:
            raise PermissionError(_friendly_error(resp, page_id))
        raise RuntimeError(_friendly_error(resp, page_id))


class ConfluenceRepository(IPageRepository):
    def __init__(self, email: str, token: str) -> None:
        self._auth = HTTPBasicAuth(email, token)
        self._headers = {"Accept": "application/json"}

    @staticmethod
    def parse_url(url: str) -> tuple[str, str]:
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
            "URL\uc5d0\uc11c page_id\ub97c \ucc3e\uc744 \uc218 \uc5c6\uc2b5\ub2c8\ub2e4.\n"
            "\uc9c0\uc6d0 \ud615\uc2dd:\n"
            "  .../wiki/spaces/SPACE/pages/123456/...\n"
            "  .../wiki/pages/viewpage.action?pageId=123456"
        )

    def _get_page(self, base_url: str, page_id: str) -> tuple[str, str]:
        url = f"{base_url}/rest/api/content/{page_id}"
        params = {"expand": "body.export_view,title"}
        resp = requests.get(
            url, headers=self._headers, auth=self._auth,
            params=params, timeout=30,
        )
        _raise_for_status(resp, page_id)
        data = resp.json()
        return data["title"], data["body"]["export_view"]["value"]

    def _get_children(self, base_url: str, page_id: str) -> list[str]:
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

    def _collect_recursive(
        self,
        base_url: str,
        page_id: str,
        include_children: bool,
        depth: int,
        progress_cb: Callable[[str], None],
    ) -> list[PageNode]:
        nodes: list[PageNode] = []
        title, html_body = self._get_page(base_url, page_id)
        progress_cb(f"[{depth}] {title}")
        nodes.append(PageNode(depth=depth, title=title, html_body=html_body))
        if include_children:
            for child_id in self._get_children(base_url, page_id):
                nodes.extend(
                    self._collect_recursive(
                        base_url, child_id, True, depth + 1, progress_cb
                    )
                )
        return nodes

    def collect(
        self,
        url: str,
        include_children: bool,
        progress_cb: Callable[[str], None],
    ) -> list[PageNode]:
        base_url, page_id = self.parse_url(url)
        return self._collect_recursive(
            base_url, page_id, include_children, 0, progress_cb
        )
