# main.py
from __future__ import annotations

import sys

try:
    import ctypes
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
        "com.confluence.parser.gui"
    )
except Exception:
    pass

from PyQt6.QtWidgets import QApplication

from infrastructure.credential_store import EnvCredentialStore
from infrastructure.confluence_repository import ConfluenceRepository
from infrastructure.converters.md_converter import MdConverter
from infrastructure.converters.docx_converter import DocxConverter
from infrastructure.converters.excel_converter import ExcelConverter
from infrastructure.converters.pdf_converter import PdfConverter
from view.main_window import MainWindow
from view.theme import QSS
from viewmodel.main_viewmodel import MainViewModel


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName("Seculayer Document Parser")
    app.setOrganizationName("Seculayer")
    app.setStyleSheet(QSS)

    cred_store = EnvCredentialStore()
    email, token = cred_store.load()
    repo = ConfluenceRepository(email, token)

    converters = {
        "md":   MdConverter(),
        "docx": DocxConverter(),
        "xlsx": ExcelConverter(),
        "pdf":  PdfConverter(),
    }

    viewmodel = MainViewModel(
        credential_store=cred_store,
        converters=converters,
        repo=repo,
    )

    win = MainWindow(viewmodel)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
