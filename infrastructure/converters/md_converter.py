# infrastructure/converters/md_converter.py
from __future__ import annotations

from bs4 import BeautifulSoup, NavigableString

from domain.model import PageNode
from domain.ports import IConverter
from infrastructure.converters.html_cleaner import clean, is_code_table, extract_code_lines


def _node_to_md(node) -> str:
    if isinstance(node, NavigableString):
        t = str(node).strip()
        return t if t else ""
    tag = node.name
    if not tag:
        return ""
    if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
        return "#" * int(tag[1]) + " " + node.get_text(strip=True) + "\n"
    if tag == "p":
        t = node.get_text().replace("\u00a0", " ").strip()
        return t + "\n" if t else ""
    if tag in ("pre", "code"):
        return "```\n" + node.get_text() + "\n```\n"
    if tag == "table":
        if is_code_table(node):
            return "```\n" + extract_code_lines(node) + "\n```\n"
        rows = node.find_all("tr")
        lines = []
        for i, row in enumerate(rows):
            cells = row.find_all(["td", "th"])
            texts = [c.get_text(strip=True).replace("|", "\\|") for c in cells]
            lines.append("| " + " | ".join(texts) + " |")
            if i == 0:
                lines.append("|" + "---|" * len(cells))
        return "\n".join(lines) + "\n"
    if tag == "ul":
        return "\n".join(
            "- " + li.get_text(strip=True)
            for li in node.find_all("li", recursive=False)
        ) + "\n"
    if tag == "ol":
        return "\n".join(
            f"{i + 1}. " + li.get_text(strip=True)
            for i, li in enumerate(node.find_all("li", recursive=False))
        ) + "\n"
    if tag in ("strong", "b"):
        return "**" + node.get_text() + "**"
    if tag in ("em", "i"):
        return "*" + node.get_text() + "*"
    if tag == "hr":
        return "---\n"
    return "".join(_node_to_md(c) for c in node.children)


class MdConverter(IConverter):
    def convert(self, pages: list[PageNode], output_path: str) -> None:
        parts: list[str] = []
        for page in pages:
            parts.append("#" * min(page.depth + 1, 6) + " " + page.title + "\n")
            soup = clean(BeautifulSoup(page.html_body, "html.parser"))
            parts.extend(_node_to_md(c) for c in soup.children)
            parts.append("\n---\n")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(parts))
