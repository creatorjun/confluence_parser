# infrastructure/converters/pdf_converter.py
from __future__ import annotations

from bs4 import BeautifulSoup, NavigableString, Tag

from domain.model import PageNode
from domain.ports import IConverter
from infrastructure.converters.html_cleaner import clean, is_code_table, extract_code_lines

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.lib.enums import TA_LEFT
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
        Table, TableStyle, Preformatted,
    )
    _REPORTLAB_OK = True
except ImportError:
    _REPORTLAB_OK = False

# ── 폰트 등록 (한글 지원) ────────────────────────────────────
_FONT_REGISTERED = False

_KOREAN_FONT_CANDIDATES = [
    # Windows 맑은 고딕
    ("C:/Windows/Fonts/malgun.ttf",    "MalgunGothic"),
    ("C:/Windows/Fonts/malgunbd.ttf",  "MalgunGothic-Bold"),
    # macOS 애플 산돌 고딕
    ("/System/Library/Fonts/AppleSDGothicNeo.ttc", "AppleSDGothicNeo"),
    # Linux 나눔고딕
    ("/usr/share/fonts/truetype/nanum/NanumGothic.ttf", "NanumGothic"),
]


def _register_korean_font() -> str:
    """Korean 폰트를 등록하고 폰트명 반환. 실패시 Helvetica 반환."""
    global _FONT_REGISTERED
    if _FONT_REGISTERED:
        return "MalgunGothic" if _font_name != "Helvetica" else "Helvetica"

    import os
    for path, name in _KOREAN_FONT_CANDIDATES:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont(name, path))
                bold_registered = False
                for bp, bn in _KOREAN_FONT_CANDIDATES:
                    if "Bold" in bn or "bd" in bp:
                        if os.path.exists(bp):
                            try:
                                pdfmetrics.registerFont(TTFont(bn, bp))
                                bold_registered = True
                            except Exception:
                                pass
                        break
                _FONT_REGISTERED = True
                globals()["_font_name"] = name
                globals()["_font_bold"] = name if not bold_registered else bn
                return name
            except Exception:
                continue
    globals()["_font_name"] = "Helvetica"
    globals()["_font_bold"] = "Helvetica-Bold"
    return "Helvetica"


_font_name = "Helvetica"
_font_bold = "Helvetica-Bold"


# ── 스타일 빌더 ────────────────────────────────────────────────────────
def _make_styles(font: str, font_bold: str) -> dict:
    base = getSampleStyleSheet()
    def ps(name, **kw) -> ParagraphStyle:
        return ParagraphStyle(name, fontName=font, **kw)

    return {
        "h1": ps("H1", fontName=font_bold, fontSize=18, textColor=colors.HexColor("#1F3864"),
                 spaceAfter=6, spaceBefore=18, borderPadding=(0,0,4,0)),
        "h2": ps("H2", fontName=font_bold, fontSize=14, textColor=colors.HexColor("#2F5496"),
                 spaceAfter=4, spaceBefore=14),
        "h3": ps("H3", fontName=font_bold, fontSize=12, textColor=colors.HexColor("#2F5496"),
                 spaceAfter=3, spaceBefore=12),
        "h4": ps("H4", fontName=font_bold, fontSize=10, textColor=colors.HexColor("#333333"),
                 spaceAfter=2, spaceBefore=10),
        "h5": ps("H5", fontName=font_bold, fontSize=10, textColor=colors.HexColor("#333333"),
                 spaceAfter=2, spaceBefore=8),
        "h6": ps("H6", fontName=font_bold, fontSize=10, textColor=colors.HexColor("#333333"),
                 spaceAfter=2, spaceBefore=6),
        "body": ps("Body", fontSize=10, leading=16, spaceAfter=4),
        "bullet": ps("Bullet", fontSize=10, leading=16, leftIndent=16,
                     bulletIndent=6, spaceAfter=2),
        "code": ParagraphStyle(
            "Code", fontName="Courier", fontSize=9, leading=13,
            backColor=colors.HexColor("#F4F4F4"),
            borderColor=colors.HexColor("#4A90D9"),
            borderWidth=0, leftIndent=12, rightIndent=4,
            spaceBefore=4, spaceAfter=4,
        ),
        "th": ParagraphStyle(
            "TH", fontName=font_bold, fontSize=9, leading=12,
            textColor=colors.white,
        ),
        "td": ps("TD", fontSize=9, leading=12),
    }


# ── HTML → Flowable 변환 ─────────────────────────────────────────────────
_TBL_HEADER_BG  = colors.HexColor("#2F5496")
_TBL_EVEN_BG    = colors.HexColor("#F2F6FC")
_TBL_BORDER     = colors.HexColor("#AAAAAA")


def _table_flowable(node: Tag, styles: dict):
    rows_html = node.find_all("tr")
    if not rows_html:
        return None

    data = []
    row_is_header = []
    for ri, tr in enumerate(rows_html):
        cells = tr.find_all(["td", "th"])
        is_hdr = any(c.name == "th" for c in cells) or ri == 0
        row_is_header.append(is_hdr)
        style = styles["th"] if is_hdr else styles["td"]
        data.append([
            Paragraph(c.get_text(strip=True).replace("&", "&amp;"), style)
            for c in cells
        ])

    if not data or not data[0]:
        return None

    col_count = max(len(r) for r in data)
    col_width = (A4[0] - 40 * mm) / col_count

    tbl = Table(data, colWidths=[col_width] * col_count, repeatRows=1)
    ts = [
        ("BACKGROUND", (0, 0), (-1, 0), _TBL_HEADER_BG),
        ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
        ("FONTNAME",   (0, 0), (-1, 0), _font_bold),
        ("FONTSIZE",   (0, 0), (-1, -1), 9),
        ("GRID",       (0, 0), (-1, -1), 0.5, _TBL_BORDER),
        ("VALIGN",     (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, _TBL_EVEN_BG]),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
    ]
    tbl.setStyle(TableStyle(ts))
    return tbl


def _node_to_flowables(node, styles: dict, story: list) -> None:
    if isinstance(node, NavigableString):
        text = str(node).strip()
        if text:
            story.append(Paragraph(text.replace("&", "&amp;"), styles["body"]))
        return

    tag = node.name
    if not tag:
        return

    if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
        text = node.get_text(strip=True).replace("&", "&amp;")
        story.append(Paragraph(text, styles[tag]))

    elif tag == "p":
        text = node.get_text().replace("\u00a0", " ").strip().replace("&", "&amp;")
        if text:
            story.append(Paragraph(text, styles["body"]))

    elif tag in ("pre", "code"):
        for line in node.get_text().splitlines():
            story.append(Preformatted(line, styles["code"]))

    elif tag == "table":
        if is_code_table(node):
            for line in extract_code_lines(node).splitlines():
                story.append(Preformatted(line, styles["code"]))
        else:
            tbl = _table_flowable(node, styles)
            if tbl:
                story.append(tbl)
                story.append(Spacer(1, 4 * mm))

    elif tag in ("ul", "ol"):
        for i, li in enumerate(node.find_all("li", recursive=False)):
            prefix = "\u2022" if tag == "ul" else f"{i + 1}."
            text = f"{prefix}  {li.get_text(strip=True).replace('&', '&amp;')}"
            story.append(Paragraph(text, styles["bullet"]))

    elif tag == "hr":
        story.append(HRFlowable(width="100%", thickness=0.5,
                                color=colors.HexColor("#DDDDDD"),
                                spaceAfter=6, spaceBefore=6))

    else:
        for child in node.children:
            _node_to_flowables(child, styles, story)


# ── Converter ───────────────────────────────────────────────────────────────
class PdfConverter(IConverter):
    def convert(self, pages: list[PageNode], output_path: str) -> None:
        if not _REPORTLAB_OK:
            raise RuntimeError(
                "reportlab가 설치되어 있지 않습니다.\n"
                "pip install reportlab 을 실행해 주세요."
            )

        font = _register_korean_font()
        font_bold = globals()["_font_bold"]
        styles = _make_styles(font, font_bold)

        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            leftMargin=18 * mm, rightMargin=18 * mm,
            topMargin=20 * mm, bottomMargin=20 * mm,
        )

        story = []
        for page in pages:
            lvl = f"h{min(page.depth + 1, 6)}"
            story.append(Paragraph(
                page.title.replace("&", "&amp;"), styles[lvl]
            ))
            soup = clean(BeautifulSoup(page.html_body, "html.parser"))
            for child in soup.children:
                _node_to_flowables(child, styles, story)
            story.append(HRFlowable(
                width="100%", thickness=1,
                color=colors.HexColor("#CCCCCC"),
                spaceAfter=10, spaceBefore=10,
            ))

        doc.build(story)
