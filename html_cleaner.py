# html_cleaner.py
from __future__ import annotations

import re
from bs4 import BeautifulSoup, Tag


def clean(soup: BeautifulSoup) -> BeautifulSoup:
    for tag in soup.find_all(["script", "style", "iframe", "object", "embed",
                               "confluence-macro", "ac:structured-macro",
                               "ac:parameter", "ac:rich-text-body"]):
        tag.decompose()

    _UNWRAP_CLASSES = [
        "confluence-information-macro", "confluence-information-macro-body",
        "confluence-information-macro-information", "confluence-information-macro-note",
        "confluence-information-macro-warning", "expand-container", "expand-content",
        "expand-control", "toc-macro", "contentLayout2", "columnLayout", "cell", "innerCell",
    ]
    for cls in _UNWRAP_CLASSES:
        for tag in soup.find_all(class_=cls):
            tag.unwrap()

    for tag in soup.find_all(class_=re.compile(
            r"(toc-macro|expand-control|page-metadata|breadcrumbs|footer|header)")):
        tag.decompose()

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

    for tag in soup.find_all(True):
        for attr in list(tag.attrs.keys()):
            if attr not in ("class", "colspan", "rowspan"):
                del tag[attr]

    for tag in soup.find_all(True):
        classes = tag.get("class", [])
        if any(c.startswith(("confluence-", "ac-", "jira-")) for c in classes):
            del tag["class"]

    for tag in soup.find_all(["span", "div"]):
        if not tag.get_text(strip=True) and not tag.find(["img", "table"]):
            tag.decompose()

    return soup


def is_code_table(table_tag: Tag) -> bool:
    rows = table_tag.find_all("tr")
    if not rows:
        return False
    col_count = max(
        sum(int(td.get("colspan", 1)) for td in row.find_all(["td", "th"]))
        for row in rows
    )
    if col_count != 1:
        return False
    return len(table_tag.find_all("p")) >= 2


def extract_code_lines(table_tag: Tag) -> str:
    lines = []
    for p in table_tag.find_all("p"):
        text = p.get_text().replace("\u00a0", " ")
        lines.append(text)
    return "\n".join(lines)
