# view/main_window.py
from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import (
    QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QCheckBox,
    QComboBox, QTextEdit, QProgressBar,
    QFileDialog, QDialog,
    QMessageBox, QFrame, QGroupBox,
    QSizePolicy, QSpacerItem,
)

from domain.ports import ICredentialStore
from view.settings_dialog import SettingsDialog
from view.theme import ACCENT, TEXT_SEC, HDR_BG, BORDER
from view.widgets import app_icon, make_divider, make_label, make_btn
from viewmodel.main_viewmodel import MainViewModel


class MainWindow(QMainWindow):
    def __init__(self, viewmodel: MainViewModel) -> None:
        super().__init__()
        self.setWindowTitle("Seculayer Document Downloader")
        self.setWindowIcon(app_icon())
        self.setMinimumSize(800, 640)
        self.resize(940, 720)

        self._vm = viewmodel
        self._cred_store: ICredentialStore = viewmodel._cred_store
        self._bind_viewmodel()
        self._build_ui()
        self._refresh_credentials(self._vm.has_credentials)

    def _bind_viewmodel(self) -> None:
        vm = self._vm
        vm.log_appended.connect(self._append_log)
        vm.progress_changed.connect(self._set_progress)
        vm.running_changed.connect(self._set_running)
        vm.convert_finished.connect(self._on_finished)
        vm.convert_error.connect(self._on_error)
        vm.credentials_changed.connect(self._refresh_credentials)

    def _build_ui(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        root_layout.addWidget(self._make_header())

        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(28, 16, 28, 16)
        cl.setSpacing(16)
        cl.addWidget(self._make_input_group())
        cl.addLayout(self._make_action_row())
        cl.addWidget(self._make_progress_widget())
        cl.addWidget(self._make_log_group())
        root_layout.addWidget(content)

        self.lbl_status = QLabel("대기 중…")
        self.lbl_status.setStyleSheet("background: transparent;")
        self.statusBar().addWidget(self.lbl_status)

    def _make_header(self) -> QWidget:
        panel = QWidget()
        panel.setObjectName("header_panel")
        panel.setFixedHeight(80)
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(24, 12, 20, 12)
        layout.setSpacing(6)

        logo_row = QHBoxLayout()
        logo_row.setSpacing(4)
        l1 = QLabel("Seculayer Document")
        l1.setObjectName("lbl_title")
        l2 = QLabel("Downloader")
        l2.setObjectName("lbl_title_accent")
        logo_row.addWidget(l1)
        logo_row.addWidget(l2)
        layout.addLayout(logo_row)
        layout.addStretch()

        self.btn_settings = make_btn("⚙  설정", "btn_secondary", height=36, min_width=90)
        self.btn_settings.clicked.connect(self._open_settings)
        layout.addWidget(self.btn_settings)
        return panel

    def _make_input_group(self) -> QGroupBox:
        grp = QGroupBox("변환 설정")
        grp.setStyleSheet("QGroupBox { background: transparent; }")
        grid = QGridLayout(grp)
        grid.setSpacing(10)
        grid.setContentsMargins(14, 20, 14, 14)
        grid.setColumnStretch(1, 1)

        _cap = lambda t: self._cap_label(t)

        grid.addWidget(_cap("Confluence 페이지 URL"), 0, 0, 1, 5)

        self.le_url = QLineEdit()
        self.le_url.setPlaceholderText(
            "https://your-instance.atlassian.net/wiki/spaces/SPACE/pages/123456/page-title"
        )
        self.le_url.setFixedHeight(40)
        grid.addWidget(self.le_url, 1, 0, 1, 5)

        grid.addWidget(_cap("출력 형식"), 2, 0)

        self.cb_format = QComboBox()
        self.cb_format.addItems([
            "📝  Markdown (.md)",
            "📄  Word (.docx)",
            "📊  Excel (.xlsx)",
            "🗂  PDF (.pdf)",
        ])
        self.cb_format.setFixedHeight(40)
        self.cb_format.setFixedWidth(200)
        grid.addWidget(self.cb_format, 2, 1)

        self.chk_children = QCheckBox("하위 문서 포함")
        self.chk_children.setChecked(True)
        grid.addWidget(self.chk_children, 2, 2)

        grid.addItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum),
            2, 3,
        )

        grid.addWidget(_cap("저장 폴더"), 3, 0)

        self.le_out = QLineEdit(self._vm.default_output_dir())
        self.le_out.setFixedHeight(40)
        self.le_out.setPlaceholderText("저장할 폴더를 선택하세요")
        grid.addWidget(self.le_out, 3, 1, 1, 3)

        btn_browse = make_btn("📂  찾기", "btn_secondary", height=40, min_width=88)
        btn_browse.clicked.connect(self._browse)
        grid.addWidget(btn_browse, 3, 4)

        self._lbl_filename_hint = QLabel("파일명: 페이지 제목에서 자동 생성됩니다")
        self._lbl_filename_hint.setStyleSheet(
            f"font-size:11px; color:{TEXT_SEC}; background:transparent;"
        )
        grid.addWidget(self._lbl_filename_hint, 4, 1, 1, 4)

        return grp

    def _make_action_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(10)
        row.addStretch()

        self.btn_run = make_btn("▶  변환 시작", height=44, min_width=148)
        self.btn_run.clicked.connect(self._start)
        row.addWidget(self.btn_run)

        self.btn_stop = make_btn("⏹  중단", "btn_danger", height=44, min_width=100)
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self._vm.stop_convert)
        row.addWidget(self.btn_stop)

        return row

    def _make_progress_widget(self) -> QWidget:
        wrapper = QWidget()
        wrapper.setStyleSheet("background:transparent;")
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        hdr = QHBoxLayout()
        hdr.addWidget(self._cap_label("진행 상태"))
        hdr.addStretch()
        self.lbl_pct = QLabel("0%")
        self.lbl_pct.setStyleSheet(
            f"font-size:11px; color:{TEXT_SEC}; background:transparent;"
        )
        hdr.addWidget(self.lbl_pct)
        layout.addLayout(hdr)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(8)
        layout.addWidget(self.progress_bar)
        return wrapper

    def _make_log_group(self) -> QGroupBox:
        grp = QGroupBox("진행 로그")
        grp.setStyleSheet("QGroupBox { background: transparent; }")
        layout = QVBoxLayout(grp)
        layout.setContentsMargins(12, 16, 12, 12)
        layout.setSpacing(0)

        self.te_log = QTextEdit()
        self.te_log.setReadOnly(True)
        self.te_log.setMinimumHeight(190)
        self.te_log.setStyleSheet("border: none;")
        layout.addWidget(self.te_log)

        return grp

    def _cap_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"font-size:11px; font-weight:600; color:{TEXT_SEC};"
            "text-transform:uppercase; background:transparent;"
        )
        return lbl

    def _open_settings(self) -> None:
        dlg = SettingsDialog(self._cred_store, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._vm.notify_credentials_updated()
            self._append_log("✅ 인증 정보가 저장되었습니다.")

    def _browse(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self,
            "저장 폴더 선택",
            self.le_out.text() or str(Path.home()),
        )
        if folder:
            self.le_out.setText(folder)

    def _start(self) -> None:
        url = self.le_url.text().strip()
        if not url:
            QMessageBox.warning(self, "입력 오류", "Confluence 페이지 URL을 입력하세요.")
            return
        if not url.startswith("http"):
            QMessageBox.warning(self, "입력 오류",
                                "URL은 http:// 또는 https://로 시작해야 합니다.")
            return
        output_dir = self.le_out.text().strip() or self._vm.default_output_dir()
        self._vm.start_convert(
            url=url,
            include_children=self.chk_children.isChecked(),
            fmt_index=self.cb_format.currentIndex(),
            output_dir=output_dir,
        )

    def _append_log(self, msg: str) -> None:
        self.te_log.append(msg)
        sb = self.te_log.verticalScrollBar()
        sb.setValue(sb.maximum())
        self.lbl_status.setText(msg[:90])

    def _set_progress(self, value: int) -> None:
        self.progress_bar.setValue(value)
        self.lbl_pct.setText(f"{value}%")

    def _set_running(self, running: bool) -> None:
        self.btn_run.setEnabled(not running)
        self.btn_stop.setEnabled(running)
        self.le_url.setEnabled(not running)
        self.cb_format.setEnabled(not running)
        self.chk_children.setEnabled(not running)

    def _refresh_credentials(self, has_cred: bool) -> None:
        if has_cred:
            self.btn_settings.setText("⚙  설정")
            self.btn_settings.setObjectName("btn_secondary")
        else:
            self.btn_settings.setText("❗ 설정 필요")
            self.btn_settings.setObjectName("btn_settings_warn")
        self.btn_settings.setStyle(self.btn_settings.style())

    def _on_finished(self, path: str) -> None:
        self.lbl_status.setText(f"완료: {Path(path).name}")
        QMessageBox.information(
            self, "변환 완료",
            f"성공적으로 변환되었습니다.\n\n저장 경로:\n{path}",
        )

    def _on_error(self, msg: str) -> None:
        self.lbl_status.setText("오류 발생")
        QMessageBox.critical(self, "오류 발생", msg)
