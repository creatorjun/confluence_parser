"""공용 위젯 팩토리 함수."""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QFrame, QLabel, QPushButton

from view.theme import ACCENT

_ICO_PATH = Path(__file__).parent.parent / "icon" / "parser.ico"


def app_icon() -> QIcon:
    if _ICO_PATH.exists():
        return QIcon(str(_ICO_PATH))
    from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont as QF
    pm = QPixmap(64, 64)
    pm.fill(QColor(ACCENT))
    p = QPainter(pm)
    p.setPen(QColor("#ffffff"))
    f = QF()
    f.setBold(True)
    f.setPixelSize(30)
    p.setFont(f)
    p.drawText(pm.rect(), Qt.AlignmentFlag.AlignCenter, "CP")
    p.end()
    return QIcon(pm)


def make_divider() -> QFrame:
    f = QFrame()
    f.setObjectName("divider")
    f.setFrameShape(QFrame.Shape.HLine)
    f.setFixedHeight(1)
    return f


def make_label(text: str, obj_name: str = "", color: str = "") -> QLabel:
    lbl = QLabel(text)
    if obj_name:
        lbl.setObjectName(obj_name)
    if color:
        lbl.setStyleSheet(f"color:{color}; background:transparent;")
    return lbl


def make_btn(
    text: str,
    obj_name: str = "",
    height: int = 36,
    min_width: int = 0,
) -> QPushButton:
    """텍스트 잘림 없는 버튼 팩토리.
    setFixedSize 대신 setFixedHeight + setMinimumWidth 사용.
    """
    btn = QPushButton(text)
    if obj_name:
        btn.setObjectName(obj_name)
    btn.setFixedHeight(height)
    if min_width:
        btn.setMinimumWidth(min_width)
    return btn
