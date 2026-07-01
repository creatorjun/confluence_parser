# view/theme.py
from __future__ import annotations

BG         = "#F7F8FA"
SURFACE    = "#FFFFFF"
SURFACE2   = "#F0F2F5"
BORDER     = "#DDE1E7"
BORDER_FOC = "#2563EB"
BORDER_BTM = "#B0B8C8"
ACCENT     = "#2563EB"
ACCENT_H   = "#1D4ED8"
ACCENT_P   = "#1E40AF"
ACCENT_DIS = "#93C5FD"
TEXT       = "#111827"
TEXT_SEC   = "#6B7280"
TEXT_HINT  = "#9CA3AF"
SUCCESS    = "#059669"
ERROR      = "#DC2626"
WARN       = "#D97706"
LOG_BG     = BG
HDR_BG     = "#FFFFFF"
STATUS_BG  = "#F0F2F5"

QSS = f"""
QWidget {{
    background: {BG};
    color: {TEXT};
    font-family: 'Malgun Gothic', 'Segoe UI', 'Apple SD Gothic Neo', sans-serif;
    font-size: 13px;
}}
QWidget#header_panel {{
    background: {HDR_BG};
    border-bottom: 1px solid {BORDER};
}}
QGroupBox {{
    background: transparent;
    border: 1px solid {BORDER};
    border-radius: 10px;
    margin-top: 10px;
    padding: 14px 14px 12px 14px;
    font-weight: 600;
    font-size: 13px;
    color: {TEXT};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 14px;
    padding: 0 6px;
    background: {BG};
    color: {TEXT_SEC};
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}}
QLineEdit {{
    background: {SURFACE};
    border: 1.5px solid {BORDER};
    border-radius: 7px;
    padding: 9px 12px;
    color: {TEXT};
    font-size: 13px;
    selection-background-color: {ACCENT};
    selection-color: #fff;
}}
QLineEdit:hover {{ border-color: #B0B8C8; }}
QLineEdit:focus {{ border-color: {BORDER_FOC}; background: {SURFACE}; }}
QLineEdit:disabled {{ background: {SURFACE2}; color: {TEXT_HINT}; }}
QComboBox {{
    background: {SURFACE};
    border: 1.5px solid {BORDER};
    border-radius: 7px;
    padding: 9px 36px 9px 12px;
    color: {TEXT};
    font-size: 13px;
    min-width: 140px;
}}
QComboBox:hover {{ border-color: #B0B8C8; }}
QComboBox:focus {{ border-color: {BORDER_FOC}; }}
QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 30px;
    border-left: 1px solid {BORDER};
    border-top-right-radius: 7px;
    border-bottom-right-radius: 7px;
    background: {SURFACE2};
}}
QComboBox::down-arrow {{
    width: 0; height: 0;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {TEXT_SEC};
    margin-top: 2px;
}}
QComboBox QAbstractItemView {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 6px;
    outline: none;
    color: {TEXT};
    selection-background-color: #EFF6FF;
    selection-color: {ACCENT};
    padding: 4px;
}}
QComboBox:disabled {{ background: {SURFACE2}; color: {TEXT_HINT}; }}
QPushButton {{
    background: {ACCENT};
    color: #ffffff;
    border: none;
    border-radius: 7px;
    padding: 9px 20px;
    font-weight: 600;
    font-size: 13px;
    letter-spacing: 0.2px;
}}
QPushButton:hover   {{ background: {ACCENT_H}; }}
QPushButton:pressed {{ background: {ACCENT_P}; }}
QPushButton:disabled {{ background: {ACCENT_DIS}; color: #fff; }}
QPushButton#btn_secondary {{
    background: {SURFACE};
    color: {TEXT};
    border: 1.5px solid {BORDER};
    border-radius: 7px;
    font-weight: 500;
}}
QPushButton#btn_secondary:hover {{
    background: {SURFACE2};
    border: 1.5px solid {BORDER_FOC};
    color: {ACCENT};
}}
QPushButton#btn_secondary:pressed {{
    background: #E0EAFE;
    border: 1.5px solid {ACCENT_P};
}}
QPushButton#btn_secondary:disabled {{
    background: {SURFACE2};
    color: {TEXT_HINT};
    border: 1.5px solid {BORDER};
}}
QPushButton#btn_settings_warn {{
    background: {SURFACE};
    color: {ERROR};
    border: 1.5px solid {ERROR};
    font-weight: 700;
    border-radius: 7px;
    padding: 6px 14px;
    font-size: 12px;
}}
QPushButton#btn_settings_warn:hover {{
    background: #FEE2E2;
    border-color: #B91C1C;
    color: #B91C1C;
}}
QPushButton#btn_settings_warn:pressed {{ background: #FECACA; }}
QPushButton#btn_danger {{
    background: #EF4444;
    color: #ffffff;
    border: none;
}}
QPushButton#btn_danger:hover   {{ background: #DC2626; }}
QPushButton#btn_danger:pressed {{ background: #B91C1C; }}
QPushButton#btn_danger:disabled {{ background: #FCA5A5; color: #fff; }}
QCheckBox {{
    spacing: 8px;
    color: {TEXT};
    background: transparent;
    font-size: 13px;
}}
QCheckBox::indicator {{
    width: 18px; height: 18px;
    border: 2px solid {BORDER};
    border-radius: 4px;
    background: {SURFACE};
}}
QCheckBox::indicator:hover  {{ border-color: {BORDER_FOC}; }}
QCheckBox::indicator:checked {{ background: {ACCENT}; border-color: {ACCENT}; image: none; }}
QCheckBox:disabled {{ color: {TEXT_HINT}; }}
QTextEdit {{
    background: {BG};
    border: 1.5px solid {BORDER};
    border-radius: 7px;
    padding: 8px 10px;
    color: {TEXT};
    font-family: 'Consolas', 'D2Coding', 'Courier New', monospace;
    font-size: 12px;
    line-height: 1.6;
}}
QProgressBar {{
    background: {SURFACE2};
    border: none;
    border-radius: 5px;
    height: 8px;
    text-align: center;
    color: transparent;
}}
QProgressBar::chunk {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {ACCENT},stop:1 #60A5FA);
    border-radius: 5px;
}}
QStatusBar {{
    background: {STATUS_BG};
    border-top: 1px solid {BORDER};
    color: {TEXT_SEC};
    font-size: 12px;
    padding: 2px 8px;
}}
QStatusBar QLabel {{
    background: transparent;
}}
QLabel#lbl_title {{
    font-size: 20px; font-weight: 700; color: {TEXT};
    background: transparent; letter-spacing: -0.3px;
}}
QLabel#lbl_title_accent {{
    font-size: 20px; font-weight: 700; color: {ACCENT};
    background: transparent; letter-spacing: -0.3px;
}}
QLabel#lbl_sub {{
    font-size: 12px; color: {TEXT_SEC}; background: transparent;
}}
QFrame#divider {{
    background: {BORDER}; border: none; max-height: 1px; min-height: 1px;
}}
QScrollBar:vertical {{
    background: {BG}; width: 8px; border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: {BORDER}; border-radius: 4px; min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{ background: #B0B8C8; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QDialog {{
    background: {BG};
}}
QMessageBox {{
    background: {BG};
}}
QMessageBox QLabel {{
    background: transparent;
    color: {TEXT};
}}
QMessageBox QPushButton {{
    min-width: 80px;
}}
"""
