# infrastructure/converters/pdf_converter.py
from __future__ import annotations

import html as hl

from bs4 import BeautifulSoup, NavigableString

from domain.model import PageNode
from domain.ports import IConverter
from infrastructure.converters.html_cleaner import clean, is_code_table, extract_code_lines

_CSS = """
@charset "UTF-8";
@page { margin: 20mm 18mm; }
body {
    font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif;
    font-size: 10pt;
    color: #1a1a1a;
    line-height: 1.6;
}
h1 {
    font-size: 18pt; color: #1F3864;
    border-bottom: 2px solid #1F3864;
    padding-bottom: 4px; margin-top: 24px;
}
h2 {
    font-size: 14pt; color: #2F5496;
    border-bottom: 1px solid #2F5496;
    padding-bottom: 2px; margin-top: 20px;
}
h3 { font-size: 12pt; color: #2F5496; margin-top: 16px; }
h4, h5, h6 { font-size: 10pt; color: #333; margin-top: 12px; }
p { margin: 6px 0; }
table {
    border-collapse: collapse;
    width: 100%;
    margin: 10px 0;
    font-size: 9pt;
}
th {
    background: #2F5496; color: #fff; font-weight: bold;
    padding: 6px 8px; border: 1px solid #aaa; text-align: left;
}
td { padding: 5px 8px; border: 1px solid #ccc; vertical-align: top; }
tr:nth-child(even) td { background: #F2F6FC; }
pre.code-block {
    background: #F4F4F4;
    border-left: 4px solid #4A90D9;
    padding: 10px 14px;
    font-family: Consolas, 'Courier New', monospace;
    font-size: 9pt;
    color: #333;
    white-space: pre-wrap;
    word-break: break-all;
    margin: 10px 0;
    border-radius: 2px;
}
ul, ol { margin: 6px 0 6px 20px; }
li { margin: 2px 0; }
hr { border: none; border-top: 1px solid #ddd; margin: 16px 0; }
"""


def _to_html(node) -> str:
    if isinstance(node, NavigableString):
        t = str(node)
        return hl.escape(t) if t.strip() else t
    tag = node.name
    if not tag:
        return ""
    if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
        return f"<{tag}>{hl.escape(node.get_text(strip=True))}</{tag}>\n"
    if tag == "p":
        inner = "".join(_to_html(c) for c in node.children)
        return f"<p>{inner}</p>\n" if inner.strip() else ""
    if tag in ("pre", "code"):
        return f'<pre class="code-block">{hl.escape(node.get_text())}</pre>\n'
    if tag == "table":
        if is_code_table(node):
            return f'<pre class="code-block">{hl.escape(extract_code_lines(node))}</pre>\n'
        rows = node.find_all("tr")
        html_rows = []
        for ri, row in enumerate(rows):
            cells = row.find_all(["td", "th"])
            cell_tags = []
            for ct in cells:
                ctype = "th" if (ct.name == "th" or ri == 0) else "td"
                cs = ct.get("colspan", "")
                span = f' colspan="{cs}"' if cs else ""
                cell_tags.append(f"<{ctype}{span}>{hl.escape(ct.get_text(strip=True))}</{ctype}>")
            html_rows.append("<tr>" + "".join(cell_tags) + "</tr>")
        return "<table>" + "".join(html_rows) + "</table>\n"
    if tag == "ul":
        items = "".join(
            f"<li>{hl.escape(li.get_text(strip=True))}</li>"
            for li in node.find_all("li", recursive=False)
        )
        return f"<ul>{items}</ul>\n"
    if tag == "ol":
        items = "".join(
            f"<li>{hl.escape(li.get_text(strip=True))}</li>"
            for li in node.find_all("li", recursive=False)
        )
        return f"<ol>{items}</ol>\n"
    if tag in ("strong", "b"):
        return f"<strong>{hl.escape(node.get_text())}</strong>"
    if tag in ("em", "i"):
        return f"<em>{hl.escape(node.get_text())}</em>"
    if tag == "hr":
        return "<hr/>\n"
    return "".join(_to_html(c) for c in node.children)


def _build_html(pages: list[PageNode]) -> str:
    body_parts: list[str] = []
    for page in pages:
        lvl = min(page.depth + 1, 6)
        body_parts.append(f"<h{lvl}>{hl.escape(page.title)}</h{lvl}>\n")
        soup = clean(BeautifulSoup(page.html_body, "html.parser"))
        for c in soup.children:
            body_parts.append(_to_html(c))
        body_parts.append("<hr/>\n")
    return (
        '<!DOCTYPE html>'
        '<html><head>'
        '<meta charset="utf-8">'
        f'<style>{_CSS}</style>'
        '</head><body>'
        + "".join(body_parts)
        + "</body></html>"
    )


class PdfConverter(IConverter):
    def convert(self, pages: list[PageNode], output_path: str) -> None:
        try:
            from weasyprint import HTML, CSS
        except ImportError:
            raise RuntimeError(
                "weasyprint가 설치되어 있지 않습니다.\n"
                "pip install weasyprint 를 실행해 주세요."
            )

        html_str = _build_html(pages)
        HTML(string=html_str).write_pdf(output_path)
