# infrastructure/converters/html_cleaner.py
from __future__ import annotations

from bs4 import BeautifulSoup, Tag

_REMOVE_TAGS = {
    "script", "style", "meta", "link", "noscript",
    "confluence-toc", "confluence-metadata",
}

# 제거 대상 클래스: 내용은 유지하고 태그만 볚겨내는(unwrap) Confluence 래퍼 클래스
_UNWRAP_CLASSES = {
    "confluence-information-macro",
    "confluence-information-macro-information",
    "confluence-information-macro-body",
    "panel",
    "panel-body",
    "expand-container",
    "expand-content",
    "contentLayout",
    "contentLayout2",
    "cell",
    "innerCell",
    "columnLayout",
    "aui-message",
}

# 클래스가 없을 때만 unwrap 하는 구조 태그
_STRUCTURAL_TAGS = {"span", "div", "section", "article", "main", "header", "footer", "nav", "aside"}


def clean(soup: BeautifulSoup) -> BeautifulSoup:
    # 1단계: 불필요 태그 완전 제거
    for tag in soup.find_all(_REMOVE_TAGS):
        tag.decompose()

    # 2단계: 래퍼 태그 unwrap
    #   • Confluence 래퍼 클래스를 가진 태그 → 런타임에 상관없이 unwrap
    #   • 구조 태그(랜덧, div 등)에 클래스가 없는 경우에만 unwrap
    for tag in soup.find_all(True):
        classes = set(tag.get("class") or [])
        has_unwrap_class = bool(classes & _UNWRAP_CLASSES)
        is_bare_structural = tag.name in _STRUCTURAL_TAGS and not classes

        if has_unwrap_class or is_bare_structural:
            tag.unwrap()

    # 3단계: 필요한 속성만 단기
    for tag in soup.find_all(True):
        for attr in list(tag.attrs):
            if attr not in ("colspan", "rowspan", "href"):
                del tag.attrs[attr]

    return soup


def is_code_table(tag: Tag) -> bool:
    classes = set(tag.get("class") or [])
    code_classes = {"code", "codeContent", "syntaxhighlighter", "highlight", "code-block"}
    if classes & code_classes:
        return True
    rows = tag.find_all("tr")
    if len(rows) == 1:
        cells = rows[0].find_all(["td", "th"])
        if len(cells) == 1:
            inner = cells[0]
            inner_classes = set(inner.get("class") or [])
            if inner_classes & code_classes:
                return True
            if inner.find("pre") or inner.find("code"):
                return True
    return False


def extract_code_lines(tag: Tag) -> str:
    pre = tag.find("pre")
    if pre:
        return pre.get_text()
    code = tag.find("code")
    if code:
        return code.get_text()
    lines = [
        cell.get_text()
        for row in tag.find_all("tr")
        for cell in row.find_all(["td", "th"])
    ]
    return "\n".join(lines)
