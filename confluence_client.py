# confluence_client.py
from __future__ import annotations

import requests
from requests.auth import HTTPBasicAuth
from config import BASE_URL, EMAIL, API_TOKEN


_auth = HTTPBasicAuth(EMAIL, API_TOKEN)
_headers = {"Accept": "application/json"}


def get_page(page_id: str) -> tuple[str, str]:
    url = f"{BASE_URL}/rest/api/content/{page_id}"
    params = {"expand": "body.export_view,title"}
    resp = requests.get(url, headers=_headers, auth=_auth, params=params)
    resp.raise_for_status()
    data = resp.json()
    return data["title"], data["body"]["export_view"]["value"]


def get_children(page_id: str) -> list[str]:
    ids: list[str] = []
    start = 0
    limit = 50
    while True:
        url = f"{BASE_URL}/rest/api/content/{page_id}/child/page"
        params = {"limit": limit, "start": start, "expand": ""}
        resp = requests.get(url, headers=_headers, auth=_auth, params=params)
        resp.raise_for_status()
        results = resp.json().get("results", [])
        ids.extend(r["id"] for r in results)
        if len(results) < limit:
            break
        start += limit
    return ids


def collect_pages(page_id: str, depth: int = 0) -> list[tuple[int, str, str]]:
    pages: list[tuple[int, str, str]] = []
    title, html_body = get_page(page_id)
    print(f"{'  ' * depth}[{depth}] {title}")
    pages.append((depth, title, html_body))
    for child_id in get_children(page_id):
        pages.extend(collect_pages(child_id, depth + 1))
    return pages
