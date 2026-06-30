# to_pdf.py
from __future__ import annotations

from bs4 import BeautifulSoup
from config import ROOT_PAGE_ID
from confluence_client import collect_pages
from html_cleaner import clean, is_code_table, extract_code_lines

OUTPUT_FILE = "output.pdf"

_CSS = """
  @charset "UTF-8";
  @page { margin: 20mm 18mm; }
  body {
    font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif;
    font-size: 10pt;
    color: #1a1a1a;
    line-height: 1.6;
  }
  h1 { font-size: 18pt; color: #1F3864; border-bottom: 2px solid #1F3864; padding-bottom: 4px; margin-top: 24px; }
  h2 { font-size: 14pt; color: #2F5496; border-bottom: 1px solid #2F5496; padding-bottom: 2px; margin-top: 20px; }
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
    background-color: #2F5496;
    color: #fff;
    font-weight: bold;
    padding: 6px 8px;
    border: 1px solid #aaa;
    text-align: left;
  }
  td {
    padding: 5px 8px;
    border: 1px solid #ccc;
    vertical-align: top;
  }
  tr:nth-child(even) td { background-color: #F2F6FC; }
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


def _node_to_html(node) -> str:
    from bs4 import NavigableString, Tag

    if isinstance(node, NavigableString):
        import html as htmllib
        text = str(node)
        return htmllib.escape(text) if text.strip() else text

    tag = node.name
    if tag is None:
        return ""

    if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
        return f"<{tag}>{node.get_text(strip=True)}</{tag}>\n"

    if tag == "p":
        inner = "".join(_node_to_html(c) for c in node.children)
        return f"<p>{inner}</p>\n" if inner.strip() else ""

    if tag in ("pre", "code"):
        import html as htmllib
        return f'<pre class="code-block">{htmllib.escape(node.get_text())}</pre>\n'

    if tag == "table":
        if is_code_table(node):
            import html as htmllib
            return f'<pre class="code-block">{htmllib.escape(extract_code_lines(node))}</pre>\n'
        rows = node.find_all("tr")
        html_rows = []
        for r_idx, row in enumerate(rows):
            cells = row.find_all(["td", "th"])
            cells_html = []
            for cell in cells:
                ct = "th" if cell.name == "th" or r_idx == 0 else "td"
                colspan = cell.get("colspan", "")
                span_attr = f' colspan="{colspan}"' if colspan else ""
                cells_html.append(f"<{ct}{span_attr}>{cell.get_text(strip=True)}</{ct}>")
            html_rows.append("<tr>" + "".join(cells_html) + "</tr>")
        return "<table>" + "".join(html_rows) + "</table>\n"

    if tag == "ul":
        items = "".join(
            f"<li>{li.get_text(strip=True)}</li>"
            for li in node.find_all("li", recursive=False)
        )
        return f"<ul>{items}</ul>\n"

    if tag == "ol":
        items = "".join(
            f"<li>{li.get_text(strip=True)}</li>"
            for li in node.find_all("li", recursive=False)
        )
        return f"<ol>{items}</ol>\n"

    if tag == "strong" or tag == "b":
        return f"<strong>{node.get_text()}</strong>"

    if tag == "em" or tag == "i":
        return f"<em>{node.get_text()}</em>"

    if tag == "hr":
        return "<hr/>\n"

    return "".join(_node_to_html(c) for c in node.children)


def build_html(pages: list[tuple[int, str, str]]) -> str:
    body_parts = []
    for depth, title, html_body in pages:
        level = min(depth + 1, 6)
        body_parts.append(f"<h{level}>{title}</h{level}>\n")
        soup = BeautifulSoup(html_body, "html.parser")
        soup = clean(soup)
        for child in soup.children:
            body_parts.append(_node_to_html(child))
        body_parts.append("<hr/>\n")

    return (
        "<!DOCTYPE html><html><head>"
        '<meta charset="utf-8">'
        f"<style>{_CSS}</style>"
        "</head><body>"
        + "".join(body_parts)
        + "</body></html>"
    )


def main():
    if not ROOT_PAGE_ID:
        print("[ERROR] CONFLUENCE_ROOT_PAGE_ID 환경변수를 설정하세요.")
        return

    try:
        import pdfkit
    except ImportError:
        print("[ERROR] pdfkit이 설치되어 있지 않습니다: pip install pdfkit")
        return

    print(f"페이지 수집 중... (root={ROOT_PAGE_ID})\n")
    pages = collect_pages(ROOT_PAGE_ID)
    print(f"\n총 {len(pages)}개 페이지 수집. PDF 생성 중...")

    html_content = build_html(pages)
    options = {
        "encoding": "utf-8",
        "enable-local-file-access": None,
        "margin-top": "20mm",
        "margin-bottom": "20mm",
        "margin-left": "18mm",
        "margin-right": "18mm",
        "page-size": "A4",
    }
    try:
        pdfkit.from_string(html_content, OUTPUT_FILE, options=options)
        print(f"완료: {OUTPUT_FILE}")
    except Exception as e:
        print(f"[ERROR] PDF 변환 실패: {e}")
        print("wkhtmltopdf 설치 여부를 확인하세요: https://wkhtmltopdf.org/downloads.html")


if __name__ == "__main__":
    main()
