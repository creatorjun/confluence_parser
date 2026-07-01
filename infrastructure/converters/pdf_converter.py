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
        HRFlowable, Table, TableStyle, Preformatted,
    )
    _REPORTLAB_OK = True
except ImportError:
    _REPORTLAB_OK = False

# ── 폰트 등록 (Windows/macOS/Linux 한글 지원) ───────────────────────────
_KOREAN_CANDIDATES = [
    ("C:/Windows/Fonts/malgun.ttf",   "MalgunGothic",
     "C:/Windows/Fonts/malgunbd.ttf", "MalgunGothic-Bold"),
    ("/System/Library/Fonts/AppleSDGothicNeo.ttc", "AppleSDGothicNeo", None, None),
    ("/usr/share/fonts/truetype/nanum/NanumGothic.ttf", "NanumGothic", None, None),
]


def _register_korean_font() -> tuple[str, str]:
    """Korean 폰트를 등록하고 (font_name, font_bold) 튜플 반환.
    등록 실패 시 Helvetica 폴백.
    """
    import os
    for path, name, bold_path, bold_name in _KOREAN_CANDIDATES:
        if not os.path.exists(path):
            continue
        try:
            pdfmetrics.registerFont(TTFont(name, path))
        except Exception:
            continue

        registered_bold = name  # 볼드 없으면 일반 폰트로 폴백
        if bold_path and bold_name and os.path.exists(bold_path):
            try:
                pdfmetrics.registerFont(TTFont(bold_name, bold_path))
                registered_bold = bold_name
            except Exception:
                pass
        return name, registered_bold

    return "Helvetica", "Helvetica-Bold"


# ── 스타일 빌더 ────────────────────────────────────────────────────────
def _make_styles(font: str, font_bold: str) -> dict:
    """주어진 폰트로 ParagraphStyle 딕셔너리 생성.

    내부 헬퍼 ps()는 별도의 fn 인수로 폰트명을 받으므로
    fontName 키워드가 **kw 에 중복 전달되는 문제가 없다.
    """
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
        # fn="Courier" 사용 — font 기본값과 충돌 없음
        "code":   ps("Code",   fn="Courier", fontSize=9, leading=13,
                     backColor=colors.HexColor("#F4F4F4"),
                     leftIndent=12, rightIndent=4,
                     spaceBefore=4, spaceAfter=4),
        "th":     ps("TH",     fn=font_bold, fontSize=9, leading=12,
                     textColor=colors.white),
        "td":     ps("TD",     fontSize=9, leading=12),
    }


# ── 테이블 Flowable ────────────────────────────────────────────────────────
_TBL_HEADER_BG = colors.HexColor("#2F5496") if _REPORTLAB_OK else None
_TBL_EVEN_BG   = colors.HexColor("#F2F6FC") if _REPORTLAB_OK else None
_TBL_BORDER    = colors.HexColor("#AAAAAA") if _REPORTLAB_OK else None


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
            Paragraph(c.get_text(strip=True).replace("&", "&amp;"), cell_style)
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
def _safe(text: str) -> str:
    return text.replace("&", "&amp;")


def _node_to_flowables(node, styles: dict, story: list) -> None:
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
            _node_to_flowables(child, styles, story)


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
                _node_to_flowables(child, styles, story)
            story.append(HRFlowable(
                width="100%", thickness=1,
                color=colors.HexColor("#CCCCCC"),
                spaceAfter=10, spaceBefore=10,
            ))

        doc.build(story)
