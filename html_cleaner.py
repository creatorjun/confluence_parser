# html_cleaner.py
"""
Confluence export_view HTML 정제 모듈
- 내부 링크/앵커 제거
- Confluence 전용 매크로/클래스 제거
- 코드 테이블 감지 (1열 다중 <p> 패턴)
"""
from __future__ import annotations

import re
from bs4 import BeautifulSoup, Tag


def clean(soup: BeautifulSoup) -> BeautifulSoup:
    # 1. 불필요 태그 삭제
    for tag in soup.find_all([
        "script", "style", "iframe", "object", "embed",
        "confluence-macro", "ac:structured-macro",
        "ac:parameter", "ac:rich-text-body",
    ]):
        tag.decompose()

    # 2. 래퍼 클래스 unwrap
    _UNWRAP = [
        "confluence-information-macro", "confluence-information-macro-body",
        "confluence-information-macro-information", "confluence-information-macro-note",
        "confluence-information-macro-warning", "expand-container", "expand-content",
        "expand-control", "toc-macro", "contentLayout2", "columnLayout", "cell", "innerCell",
    ]
    for cls in _UNWRAP:
        for tag in soup.find_all(class_=cls):
            tag.unwrap()

    # 3. 메타/네비 요소 삭제
    for tag in soup.find_all(class_=re.compile(
            r"(toc-macro|expand-control|page-metadata|breadcrumbs|footer|header)")):
        tag.decompose()

    # 4. 링크 처리
    for a_tag in soup.find_all("a"):
        href = a_tag.get("href", "")
        is_internal = (
            href.startswith("/")
            or href.startswith("#")
            or "atlassian.net/wiki" in href
            or "atlassian.net/pages" in href
        )
        if is_internal:
            a_tag.unwrap()
        else:
            for attr in ("href", "class", "target"):
                if a_tag.has_attr(attr):
                    del a_tag[attr]

    # 5. 불필요 속성 제거 (colspan/rowspan만 유지)
    for tag in soup.find_all(True):
        for attr in list(tag.attrs.keys()):
            if attr not in ("class", "colspan", "rowspan"):
                del tag[attr]

    # 6. Confluence CSS 클래스 제거
    for tag in soup.find_all(True):
        classes = tag.get("class", [])
        if any(c.startswith(("confluence-", "ac-", "jira-")) for c in classes):
            del tag["class"]

    # 7. 빈 span/div 제거
    for tag in soup.find_all(["span", "div"]):
        if not tag.get_text(strip=True) and not tag.find(["img", "table"]):
            tag.decompose()

    return soup


def is_code_table(table_tag: Tag) -> bool:
    """1열 테이블에 <p>가 2개 이상이면 코드 블록으로 판단"""
    rows = table_tag.find_all("tr")
    if not rows:
        return False
    col_count = max(
        sum(int(td.get("colspan", 1)) for td in row.find_all(["td", "th"]))
        for row in rows
    )
    return col_count == 1 and len(table_tag.find_all("p")) >= 2


def extract_code_lines(table_tag: Tag) -> str:
    lines = []
    for p in table_tag.find_all("p"):
        lines.append(p.get_text().replace("\u00a0", " "))
    return "\n".join(lines)
