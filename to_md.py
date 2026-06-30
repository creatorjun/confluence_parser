# to_md.py
from __future__ import annotations

from bs4 import BeautifulSoup
from config import ROOT_PAGE_ID
from confluence_client import collect_pages
from html_cleaner import clean, is_code_table, extract_code_lines

OUTPUT_FILE = "output.md"


def _table_to_md(table_tag) -> str:
    rows = table_tag.find_all("tr")
    if not rows:
        return ""
    lines = []
    for i, row in enumerate(rows):
        cells = row.find_all(["td", "th"])
        cell_texts = [c.get_text(strip=True).replace("|", "\\|") for c in cells]
        lines.append("| " + " | ".join(cell_texts) + " |")
        if i == 0:
            lines.append("|" + "---|" * len(cells))
    return "\n".join(lines)


def _node_to_md(node, depth: int = 0) -> str:
    from bs4 import NavigableString, Tag

    if isinstance(node, NavigableString):
        text = str(node).strip()
        return text if text else ""

    tag = node.name
    if tag is None:
        return ""

    if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
        level = int(tag[1])
        return "#" * level + " " + node.get_text(strip=True) + "\n"

    if tag == "p":
        text = node.get_text().replace("\u00a0", " ").strip()
        return text + "\n" if text else ""

    if tag in ("pre", "code"):
        return "```\n" + node.get_text() + "\n```\n"

    if tag == "table":
        if is_code_table(node):
            code = extract_code_lines(node)
            return "```\n" + code + "\n```\n"
        return _table_to_md(node) + "\n"

    if tag == "ul":
        items = []
        for li in node.find_all("li", recursive=False):
            items.append("- " + li.get_text(strip=True))
        return "\n".join(items) + "\n"

    if tag == "ol":
        items = []
        for i, li in enumerate(node.find_all("li", recursive=False), 1):
            items.append(f"{i}. " + li.get_text(strip=True))
        return "\n".join(items) + "\n"

    if tag == "strong" or tag == "b":
        return "**" + node.get_text() + "**"

    if tag == "em" or tag == "i":
        return "*" + node.get_text() + "*"

    if tag == "hr":
        return "---\n"

    parts = []
    for child in node.children:
        parts.append(_node_to_md(child, depth))
    return "".join(parts)


def build_md(pages: list[tuple[int, str, str]]) -> str:
    sections = []
    for depth, title, html_body in pages:
        heading_level = min(depth + 1, 6)
        sections.append("#" * heading_level + " " + title + "\n")
        soup = BeautifulSoup(html_body, "html.parser")
        soup = clean(soup)
        for child in soup.children:
            sections.append(_node_to_md(child))
        sections.append("\n---\n")
    return "\n".join(sections)


def main():
    if not ROOT_PAGE_ID:
        print("[ERROR] CONFLUENCE_ROOT_PAGE_ID 환경변수를 설정하세요.")
        return
    print(f"페이지 수집 중... (root={ROOT_PAGE_ID})\n")
    pages = collect_pages(ROOT_PAGE_ID)
    print(f"\n총 {len(pages)}개 페이지 수집. Markdown 생성 중...")
    md_text = build_md(pages)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(md_text)
    print(f"완료: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
