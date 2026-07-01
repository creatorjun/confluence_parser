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

# ── 특수문자 안전 대체 테이블 ────────────────────────────────────────────────────
# Courier 폰트가 렌더링 못 하는 박스 드로잉/특수 문자를 ASCII 돱가로 대체
_CHAR_FALLBACK: dict[str, str] = {
    # 박스 드로잉 (트리 구조)
    "\u251c": "|",   # ├
    "\u2514": "+",   # └
    "\u2502": "|",   # │
    "\u2500": "-",   # ─
    "\u2510": "+",   # ┐
    "\u250c": "+",   # ┌
    "\u2518": "+",   # ┘
    "\u253c": "+",   # ┼
    "\u252c": "+",   # ┬
    "\u2534": "+",   # ┴
    "\u2524": "|",   # ┤
    "\u251c\u2500\u2500": "|--",  # ├──
    "\u2514\u2500\u2500": "+--",  # └──
    # 화살표 류
    "\u2192": "->",  # →
    "\u2190": "<-",  # ←
    "\u2191": "^",   # ↑
    "\u2193": "v",   # ↓
    "\u21d2": "=>",  # ⇒
    "\u21d0": "<=",  # ⇐
    # 체크/실패 마크
    "\u2705": "[OK]",   # ✅
    "\u274c": "[X]",    # ❌
    "\u26a0": "[!]",    # ⚠
    "\u2714": "[v]",    # ✔
    "\u2718": "[x]",    # ✘
    # 기타 자주 쓰이는 유니코드
    "\u00a0": " ",   # NBSP
    "\u2022": "*",   # • bullet
    "\u25b6": ">",   # ▶
    "\u23f9": "[]",  # ⏹
    "\u2014": "--",  # — em dash
    "\u2013": "-",   # – en dash
    "\u2026": "...", # …
}


def _safe_code(text: str) -> str:
    """코드 블록 텍스트를 Courier 안전 문자열로 변환.
    한글 폰트 사용 시에는 불필요하지만,
    Courier 보종을 위해 유니코드 문자를 충분히 대체한다.
    """
    for char, replacement in _CHAR_FALLBACK.items():
        text = text.replace(char, replacement)
    return text


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

        registered_bold = name
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
        # 코드 블록: 한글 폰트를 사용하여 특수문자 깨짐 방지
        # Courier 를 쓰면 박스드로잉 문자(├─└ 등)가 깨질 수 있음
        "code":   ps("Code",   fontSize=9, leading=13,
                     backColor=colors.HexColor("#F4F4F4"),
                     leftIndent=12, rightIndent=4,
                     spaceBefore=2, spaceAfter=2),
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


# ── 공통 헬퍼 ─────────────────────────────────────────────────────────────
def _safe(text: str) -> str:
    """ReportLab Paragraph XML 특수문자 이스케이프."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _code_lines(text: str, style: ParagraphStyle) -> list:
    """코드 텍스트를 줄단위 Paragraph 리스트로 변환.
    한글 폰트를 사용하므로 맑은 고딕/코드 등 모든 특수문자가 정상 출력.
    한글 폰트에 없는 문자는 _safe_code()에서 ASCII로 대체.
    """
    result = []
    for line in _safe_code(text).splitlines():
        escaped = _safe(line) if line.strip() else "\u00a0"
        result.append(Paragraph(
            f'<font face="Courier">{escaped}</font>',
            style,
        ))
    return result


# ── HTML → Flowable 변환 ─────────────────────────────────────────────────
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
        story.extend(_code_lines(node.get_text(), styles["code"]))

    elif tag == "table":
        if is_code_table(node):
            story.extend(_code_lines(extract_code_lines(node), styles["code"]))
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
