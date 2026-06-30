# converters/to_pdf.py
from __future__ import annotations

from bs4 import BeautifulSoup, NavigableString
from html_cleaner import clean, is_code_table, extract_code_lines

_CSS = """
@charset "UTF-8";
@page { margin: 20mm 18mm; }
body { font-family:'Malgun Gothic','Apple SD Gothic Neo',sans-serif;
       font-size:10pt; color:#1a1a1a; line-height:1.6; }
h1 { font-size:18pt; color:#1F3864; border-bottom:2px solid #1F3864;
     padding-bottom:4px; margin-top:24px; }
h2 { font-size:14pt; color:#2F5496; border-bottom:1px solid #2F5496;
     padding-bottom:2px; margin-top:20px; }
h3 { font-size:12pt; color:#2F5496; margin-top:16px; }
h4,h5,h6 { font-size:10pt; color:#333; margin-top:12px; }
p { margin:6px 0; }
table { border-collapse:collapse; width:100%; margin:10px 0; font-size:9pt; }
th { background:#2F5496; color:#fff; font-weight:bold;
     padding:6px 8px; border:1px solid #aaa; text-align:left; }
td { padding:5px 8px; border:1px solid #ccc; vertical-align:top; }
tr:nth-child(even) td { background:#F2F6FC; }
pre.code-block { background:#F4F4F4; border-left:4px solid #4A90D9;
    padding:10px 14px; font-family:Consolas,'Courier New',monospace;
    font-size:9pt; color:#333; white-space:pre-wrap;
    word-break:break-all; margin:10px 0; border-radius:2px; }
ul,ol { margin:6px 0 6px 20px; }
li { margin:2px 0; }
hr { border:none; border-top:1px solid #ddd; margin:16px 0; }
"""


def _to_html(node) -> str:
    import html as hl
    if isinstance(node, NavigableString):
        t = str(node)
        return hl.escape(t) if t.strip() else t
    tag = node.name
    if not tag: return ""
    if tag in ("h1","h2","h3","h4","h5","h6"):
        return f"<{tag}>{node.get_text(strip=True)}</{tag}>\n"
    if tag == "p":
        inner = "".join(_to_html(c) for c in node.children)
        return f"<p>{inner}</p>\n" if inner.strip() else ""
    if tag in ("pre","code"):
        return f'<pre class="code-block">{hl.escape(node.get_text())}</pre>\n'
    if tag == "table":
        if is_code_table(node):
            return f'<pre class="code-block">{hl.escape(extract_code_lines(node))}</pre>\n'
        rows = node.find_all("tr")
        html_rows = []
        for ri, row in enumerate(rows):
            cells = row.find_all(["td","th"])
            cts = []
            for ct in cells:
                ctype = "th" if (ct.name=="th" or ri==0) else "td"
                cs = ct.get("colspan","")
                sp = f' colspan="{cs}"' if cs else ""
                cts.append(f"<{ctype}{sp}>{ct.get_text(strip=True)}</{ctype}>")
            html_rows.append("<tr>" + "".join(cts) + "</tr>")
        return "<table>" + "".join(html_rows) + "</table>\n"
    if tag == "ul":
        items = "".join(f"<li>{li.get_text(strip=True)}</li>"
                        for li in node.find_all("li",recursive=False))
        return f"<ul>{items}</ul>\n"
    if tag == "ol":
        items = "".join(f"<li>{li.get_text(strip=True)}</li>"
                        for li in node.find_all("li",recursive=False))
        return f"<ol>{items}</ol>\n"
    if tag in ("strong","b"): return f"<strong>{node.get_text()}</strong>"
    if tag in ("em","i"): return f"<em>{node.get_text()}</em>"
    if tag == "hr": return "<hr/>\n"
    return "".join(_to_html(c) for c in node.children)


def convert(pages: list[tuple[int,str,str]], output_path: str) -> None:
    try:
        import pdfkit
    except ImportError:
        raise RuntimeError("pdfkit가 설치되어 있지 않습니다: pip install pdfkit")

    body = []
    for depth, title, html_body in pages:
        lvl = min(depth+1, 6)
        body.append(f"<h{lvl}>{title}</h{lvl}>\n")
        soup = clean(BeautifulSoup(html_body, "html.parser"))
        for c in soup.children: body.append(_to_html(c))
        body.append("<hr/>\n")

    html_str = (
        '<!DOCTYPE html><html><head><meta charset="utf-8">'
        f"<style>{_CSS}</style></head><body>"
        + "".join(body) + "</body></html>"
    )
    options = {
        "encoding": "utf-8",
        "enable-local-file-access": None,
        "margin-top": "20mm", "margin-bottom": "20mm",
        "margin-left": "18mm", "margin-right": "18mm",
        "page-size": "A4",
    }
    pdfkit.from_string(html_str, output_path, options=options)
