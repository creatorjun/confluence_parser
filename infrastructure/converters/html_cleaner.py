# infrastructure/converters/html_cleaner.py
from __future__ import annotations

from bs4 import BeautifulSoup, NavigableString, Tag

_REMOVE_TAGS = {
    "script", "style", "meta", "link", "noscript",
    "confluence-toc", "confluence-metadata",
}
_UNWRAP_TAGS = {
    "span", "div", "section", "article", "main",
    "header", "footer", "nav", "aside",
}
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


def clean(soup: BeautifulSoup) -> BeautifulSoup:
    for tag in soup.find_all(_REMOVE_TAGS):
        tag.decompose()

    for tag in soup.find_all(True):
        classes = set(tag.get("class") or [])
        if tag.name in _UNWRAP_TAGS and not classes.intersection(_UNWRAP_CLASSES):
            tag.unwrap()
        elif classes.intersection(_UNWRAP_CLASSES):
            tag.unwrap()

    for tag in soup.find_all(True):
        for attr in list(tag.attrs):
            if attr not in ("colspan", "rowspan", "href"):
                del tag.attrs[attr]

    return soup


def is_code_table(tag: Tag) -> bool:
    classes = set(tag.get("class") or [])
    code_classes = {"code", "codeContent", "syntaxhighlighter", "highlight", "code-block"}
    if classes.intersection(code_classes):
        return True
    rows = tag.find_all("tr")
    if len(rows) == 1:
        cells = rows[0].find_all(["td", "th"])
        if len(cells) == 1:
            inner = cells[0]
            inner_classes = set(inner.get("class") or [])
            if inner_classes.intersection(code_classes):
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
    rows = tag.find_all("tr")
    lines = []
    for row in rows:
        for cell in row.find_all(["td", "th"]):
            text = cell.get_text()
            lines.append(text)
    return "\n".join(lines)
