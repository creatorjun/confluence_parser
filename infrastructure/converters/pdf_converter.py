# infrastructure/converters/pdf_converter.py
from __future__ import annotations

from bs4 import BeautifulSoup, NavigableString, Tag

from domain.model import PageNode
from domain.ports import IConverter
from infrastructure.converters.html_cleaner import clean, is_code_table, extract_code_lines

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer,
        HRFlowable, Table, TableStyle,
    )
    _REPORTLAB_OK = True
except ImportError:
    _REPORTLAB_OK = False

# ── 특수문자 ASCII 대체 테이블 ──────────────────────────────────────────────
# Courier 폰트가 지원하지 못하는 박스 드로잉 문자 등 ASCII로 선교체
_CHAR_FALLBACK: dict[str, str] = {
    "\u251c": "|",  "\u2514": "+",  "\u2502": "|",  "\u2500": "-",
    "\u2510": "+",  "\u250c": "+",  "\u2518": "+",  "\u253c": "+",
    "\u252c": "+",  "\u2534": "+",  "\u2524": "|",
    "\u2192": "->", "\u2190": "<-", "\u2191": "^",  "\u2193": "v",
    "\u21d2": "=>", "\u21d0": "<=",
    "\u2705": "[OK]","\u274c": "[X]", "\u26a0": "[!]",
    "\u2714": "[v]", "\u2718": "[x]",
    "\u00a0": " ",  "\u2022": "*",  "\u25b6": ">",
    "\u23f9": "[]", "\u2014": "--",  "\u2013": "-",  "\u2026": "...",
}


def _apply_char_fallback(text: str) -> str:
    for ch, rep in _CHAR_FALLBACK.items():
        text = text.replace(ch, rep)
    return text


# ── 폰트 등록 ───────────────────────────────────────────────────────────────
_KOREAN_CANDIDATES = [
    ("C:/Windows/Fonts/malgun.ttf",   "MalgunGothic",
     "C:/Windows/Fonts/malgunbd.ttf", "MalgunGothic-Bold"),
    ("/System/Library/Fonts/AppleSDGothicNeo.ttc", "AppleSDGothicNeo", None, None),
    ("/usr/share/fonts/truetype/nanum/NanumGothic.ttf", "NanumGothic", None, None),
]


def _register_korean_font() -> tuple[str, str]:
    import os
    for path, name, bold_path, bold_name in _KOREAN_CANDIDATES:
        if not os.path.exists(path):
            continue
        try:
            pdfmetrics.registerFont(TTFont(name, path))
        except Exception:
            continue
        registered_bold = name
        if bold_path and bold_name and os.path.exists(bold_path):
            try:
                pdfmetrics.registerFont(TTFont(bold_name, bold_path))
                registered_bold = bold_name
            except Exception:
                pass
        return name, registered_bold
    return "Helvetica", "Helvetica-Bold"


# ── 코드줄 렌더링 ───────────────────────────────────────────────────────────

def _is_ascii_printable(ch: str) -> bool:
    return ord(ch) < 128


def _xml_escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _build_mixed_line(line: str, korean_font: str) -> str:
    """줄 텍스트를 ASCII 구간(Courier)과 non-ASCII 구간(한글폰트)로
    분리하여 ReportLab XML 태그 문자열로 반환한다.

    예)
      "|-- gui.py  # PyQt6 메인"
      → '<font face="Courier">|-- gui.py  # PyQt6 </font>
          <font face="MalgunGothic">메인</font>'
    """
    if not line:
        return "\u00a0"  # 빈 줄: 공백 하나로 놀이 출력

    segments: list[tuple[bool, str]] = []  # (is_ascii, chunk)
    current_ascii = _is_ascii_printable(line[0])
    buf = line[0]

    for ch in line[1:]:
        ch_ascii = _is_ascii_printable(ch)
        if ch_ascii == current_ascii:
            buf += ch
        else:
            segments.append((current_ascii, buf))
            current_ascii = ch_ascii
            buf = ch
    segments.append((current_ascii, buf))

    parts: list[str] = []
    for is_ascii, chunk in segments:
        escaped = _xml_escape(chunk)
        if is_ascii:
            parts.append(f'<font face="Courier">{escaped}</font>')
        else:
            parts.append(f'<font face="{korean_font}">{escaped}</font>')
    return "".join(parts)


def _code_lines(text: str, style: ParagraphStyle, korean_font: str) -> list:
    """코드 텍스트를 줄단위 Paragraph 리스트로 변환.
    - ASCII 범위 문자 → Courier (모노스페이스 유지)
    - 한글 등 non-ASCII → korean_font (한글 정상 출력)
    - 박스드로잉 등 Courier가 못 규는 유니코드는 _apply_char_fallback으로 선수정
    """
    result = []
    for line in _apply_char_fallback(text).splitlines():
        xml = _build_mixed_line(line, korean_font)
        result.append(Paragraph(xml, style))
    return result


# ── 스타일 빌더 ────────────────────────────────────────────────────────
def _make_styles(font: str, font_bold: str) -> dict:
    def ps(name: str, fn: str | None = None, **kw) -> ParagraphStyle:
        return ParagraphStyle(name, fontName=fn or font, **kw)

    return {
        "h1": ps("H1", fn=font_bold, fontSize=18,
                 textColor=colors.HexColor("#1F3864"),
                 spaceAfter=6, spaceBefore=18),
        "h2": ps("H2", fn=font_bold, fontSize=14,
                 textColor=colors.HexColor("#2F5496"),
                 spaceAfter=4, spaceBefore=14),
        "h3": ps("H3", fn=font_bold, fontSize=12,
                 textColor=colors.HexColor("#2F5496"),
                 spaceAfter=3, spaceBefore=12),
        "h4": ps("H4", fn=font_bold, fontSize=10,
                 textColor=colors.HexColor("#333333"),
                 spaceAfter=2, spaceBefore=10),
        "h5": ps("H5", fn=font_bold, fontSize=10,
                 textColor=colors.HexColor("#333333"),
                 spaceAfter=2, spaceBefore=8),
        "h6": ps("H6", fn=font_bold, fontSize=10,
                 textColor=colors.HexColor("#333333"),
                 spaceAfter=2, spaceBefore=6),
        "body":   ps("Body",   fontSize=10, leading=16, spaceAfter=4),
        "bullet": ps("Bullet", fontSize=10, leading=16,
                     leftIndent=16, bulletIndent=6, spaceAfter=2),
        # 코드 블록: 한글폰트 기반, 공백은 일반 폰트와 동일하게 9pt
        "code":   ps("Code",   fontSize=9, leading=13,
                     backColor=colors.HexColor("#F4F4F4"),
                     leftIndent=12, rightIndent=4,
                     spaceBefore=1, spaceAfter=1),
        "th":     ps("TH",     fn=font_bold, fontSize=9, leading=12,
                     textColor=colors.white),
        "td":     ps("TD",     fontSize=9, leading=12),
    }


# ── 테이블 Flowable ────────────────────────────────────────────────────────
_TBL_HEADER_BG = colors.HexColor("#2F5496") if _REPORTLAB_OK else None
_TBL_EVEN_BG   = colors.HexColor("#F2F6FC") if _REPORTLAB_OK else None
_TBL_BORDER    = colors.HexColor("#AAAAAA") if _REPORTLAB_OK else None


def _safe(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _table_flowable(node: Tag, styles: dict):
    rows_html = node.find_all("tr")
    if not rows_html:
        return None
    data = []
    for ri, tr in enumerate(rows_html):
        cells = tr.find_all(["td", "th"])
        is_hdr = any(c.name == "th" for c in cells) or ri == 0
        cell_style = styles["th"] if is_hdr else styles["td"]
        data.append([
            Paragraph(_safe(c.get_text(strip=True)), cell_style)
            for c in cells
        ])
    if not data or not data[0]:
        return None
    col_count = max(len(r) for r in data)
    col_width  = (A4[0] - 40 * mm) / col_count
    tbl = Table(data, colWidths=[col_width] * col_count, repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  _TBL_HEADER_BG),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
        ("FONTSIZE",      (0, 0), (-1, -1), 9),
        ("GRID",          (0, 0), (-1, -1), 0.5, _TBL_BORDER),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.white, _TBL_EVEN_BG]),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
    ]))
    return tbl


# ── HTML → Flowable 변환 ─────────────────────────────────────────────────
def _node_to_flowables(
    node, styles: dict, story: list, korean_font: str
) -> None:
    if isinstance(node, NavigableString):
        text = str(node).strip()
        if text:
            story.append(Paragraph(_safe(text), styles["body"]))
        return

    tag = node.name
    if not tag:
        return

    if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
        story.append(Paragraph(_safe(node.get_text(strip=True)), styles[tag]))

    elif tag == "p":
        text = node.get_text().replace("\u00a0", " ").strip()
        if text:
            story.append(Paragraph(_safe(text), styles["body"]))

    elif tag in ("pre", "code"):
        story.extend(_code_lines(node.get_text(), styles["code"], korean_font))

    elif tag == "table":
        if is_code_table(node):
            story.extend(_code_lines(extract_code_lines(node), styles["code"], korean_font))
        else:
            tbl = _table_flowable(node, styles)
            if tbl:
                story.append(tbl)
                story.append(Spacer(1, 4 * mm))

    elif tag in ("ul", "ol"):
        for i, li in enumerate(node.find_all("li", recursive=False)):
            prefix = "\u2022" if tag == "ul" else f"{i + 1}."
            story.append(
                Paragraph(
                    f"{prefix}\u00a0\u00a0{_safe(li.get_text(strip=True))}",
                    styles["bullet"],
                )
            )

    elif tag == "hr":
        story.append(HRFlowable(
            width="100%", thickness=0.5,
            color=colors.HexColor("#DDDDDD"),
            spaceAfter=6, spaceBefore=6,
        ))

    else:
        for child in node.children:
            _node_to_flowables(child, styles, story, korean_font)


# ── Converter ───────────────────────────────────────────────────────────────
class PdfConverter(IConverter):
    def convert(self, pages: list[PageNode], output_path: str) -> None:
        if not _REPORTLAB_OK:
            raise RuntimeError(
                "reportlab가 설치되어 있지 않습니다.\n"
                "pip install reportlab 을 실행해 주세요."
            )

        font, font_bold = _register_korean_font()
        styles = _make_styles(font, font_bold)

        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            leftMargin=18 * mm, rightMargin=18 * mm,
            topMargin=20 * mm, bottomMargin=20 * mm,
        )

        story: list = []
        for page in pages:
            lvl = f"h{min(page.depth + 1, 6)}"
            story.append(Paragraph(_safe(page.title), styles[lvl]))
            soup = clean(BeautifulSoup(page.html_body, "html.parser"))
            for child in soup.children:
                _node_to_flowables(child, styles, story, font)
            story.append(HRFlowable(
                width="100%", thickness=1,
                color=colors.HexColor("#CCCCCC"),
                spaceAfter=10, spaceBefore=10,
            ))

        doc.build(story)
