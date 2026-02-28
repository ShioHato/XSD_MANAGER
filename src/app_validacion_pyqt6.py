import sys
from pathlib import Path
import ctypes
import re

from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QColor, QFont, QIcon, QBrush
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

try:
    from .validar_xml import ValidationIssue, validate
except ImportError:
    from validar_xml import ValidationIssue, validate


def resource_path(filename: str) -> Path:
    if hasattr(sys, "_MEIPASS"):
        base = Path(getattr(sys, "_MEIPASS"))
        candidates = [
            base / "assets" / "icons" / filename,
            base / filename,
        ]
    else:
        project_root = Path(__file__).resolve().parent.parent
        candidates = [
            project_root / "assets" / "icons" / filename,
            project_root / filename,
        ]

    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def build_app_icon() -> QIcon:
    icon = QIcon()
    ico_path = resource_path("xsd_app_icon.ico")

    if ico_path.exists():
        # Multi-size ICO is ideal for title bar/taskbar small and medium sizes.
        icon.addFile(str(ico_path))

    return icon


def set_windows_app_id() -> None:
    if sys.platform != "win32":
        return
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("XSDManager")
    except Exception:
        # If this fails, window icon still works; taskbar may keep python icon.
        pass


class StatCard(QFrame):
    def __init__(self, title: str, accent: str) -> None:
        super().__init__()
        self.setObjectName("StatCard")
        self.setProperty("accent", accent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(4)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("CardTitle")

        self.value_label = QLabel("0")
        self.value_label.setObjectName("CardValue")

        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)

    def set_value(self, value: int) -> None:
        self.value_label.setText(str(value))


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.settings = QSettings()
        self.last_xml_line = 0
        self.setWindowTitle("XSD MANAGER")
        self.resize(1040, 680)
        app_icon = build_app_icon()
        if not app_icon.isNull():
            self.setWindowIcon(app_icon)

        central = QWidget()
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(12)
        top_bar = QFrame()
        top_bar.setObjectName("TopBar")
        top_layout = QVBoxLayout(top_bar)
        top_layout.setContentsMargins(16, 14, 16, 14)
        top_layout.setSpacing(2)

        title = QLabel("Validador de XML")
        title.setObjectName("MainTitle")
        subtitle = QLabel("Validacion estructural dado un XSD, con clasificacion de ERRORES y AVISOS")
        subtitle.setObjectName("Subtitle")

        top_layout.addWidget(title)
        top_layout.addWidget(subtitle)
        root.addWidget(top_bar)

        self.xml_input = QLineEdit()
        self.xsd_input = QLineEdit()

        self.xml_input.setPlaceholderText("Selecciona un archivo XML...")
        self.xsd_input.setPlaceholderText("Selecciona un archivo XSD...")

        self._build_file_row(root, "XSD", self.xsd_input, self.pick_xsd)
        self._build_file_row(root, "XML", self.xml_input, self.pick_xml)

        actions = QHBoxLayout()
        actions.setSpacing(8)
        self.chk_auto_validate = QCheckBox("Validacion automatica")
        self.chk_auto_validate.setChecked(True)
        self.chk_auto_validate.toggled.connect(self._on_auto_validate_toggled)

        self.btn_validate = QPushButton("Validar")
        self.btn_validate.clicked.connect(self.run_validation)

        self.btn_clear = QPushButton("Limpiar")
        self.btn_clear.setObjectName("Secondary")
        self.btn_clear.clicked.connect(self.clear_results)

        actions.addWidget(self.btn_validate)
        actions.addWidget(self.btn_clear)
        actions.addStretch(1)
        actions.addWidget(self.chk_auto_validate)

        root.addLayout(actions)

        cards = QGridLayout()
        cards.setHorizontalSpacing(10)
        cards.setVerticalSpacing(10)

        self.card_total = StatCard("Incidencias", "neutral")
        self.card_errors = StatCard("Errores", "error")
        self.card_warnings = StatCard("Avisos", "warning")

        cards.addWidget(self.card_total, 0, 0)
        cards.addWidget(self.card_errors, 0, 1)
        cards.addWidget(self.card_warnings, 0, 2)
        root.addLayout(cards)

        self.status = QLabel("Listo para validar.")
        self.status.setObjectName("StatusLabel")
        self.status.hide()

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Nivel", "Linea", "Columna", "Mensaje"])
        h_header = self.table.horizontalHeader()
        if h_header is not None:
            h_header.setStretchLastSection(True)
            h_header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            h_header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
            h_header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
            h_header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)

        v_header = self.table.verticalHeader()
        if v_header is not None:
            v_header.setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.setWordWrap(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        root.addWidget(self.table, 1)

        self.apply_styles()
        self._load_last_paths()
        self._maybe_auto_validate()

    def showEvent(self, a0) -> None:
        super().showEvent(a0)
        self._apply_windows_dark_title_bar()

    def _apply_windows_dark_title_bar(self) -> None:
        if sys.platform != "win32":
            return
        try:
            hwnd = int(self.winId())
            value = ctypes.c_int(1)
            # Windows 10/11 use attribute 20; some builds use 19.
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1 = 19
            DWMWA_BORDER_COLOR = 34
            DWMWA_CAPTION_COLOR = 35
            DWMWA_TEXT_COLOR = 36
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_USE_IMMERSIVE_DARK_MODE,
                ctypes.byref(value),
                ctypes.sizeof(value),
            )
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1,
                ctypes.byref(value),
                ctypes.sizeof(value),
            )
            # Caption tone close to VS Code dark gray.
            caption_gray = ctypes.c_int(0x2B2B2B)
            text_white = ctypes.c_int(0xFFFFFF)
            border_gray = ctypes.c_int(0x3A3A3A)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_CAPTION_COLOR,
                ctypes.byref(caption_gray),
                ctypes.sizeof(caption_gray),
            )
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_TEXT_COLOR,
                ctypes.byref(text_white),
                ctypes.sizeof(text_white),
            )
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_BORDER_COLOR,
                ctypes.byref(border_gray),
                ctypes.sizeof(border_gray),
            )
        except Exception:
            pass

    def _build_file_row(self, parent_layout: QVBoxLayout, label_text: str, line_edit: QLineEdit, pick_fn) -> None:
        row = QHBoxLayout()
        row.setSpacing(8)

        label = QLabel(label_text)
        label.setObjectName("FieldLabel")
        label.setMinimumWidth(40)

        button = QPushButton("Examinar")
        button.setObjectName("Secondary")
        button.clicked.connect(pick_fn)

        row.addWidget(label)
        row.addWidget(line_edit, 1)
        row.addWidget(button)
        parent_layout.addLayout(row)

    def pick_xml(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Seleccionar XML", "", "XML (*.xml);;Todos (*.*)")
        if path:
            self.xml_input.setText(path)
            self._save_preferences()
            self._maybe_auto_validate()

    def pick_xsd(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Seleccionar XSD", "", "XSD (*.xsd);;Todos (*.*)")
        if path:
            self.xsd_input.setText(path)
            self._save_preferences()
            self._maybe_auto_validate()

    def _load_last_paths(self) -> None:
        xml_path = self.settings.value("last_xml_path", "", str)
        xsd_path = self.settings.value("last_xsd_path", "", str)
        auto_validate = self.settings.value("auto_validate", True, bool)
        self.chk_auto_validate.setChecked(auto_validate)

        if xml_path and Path(xml_path).exists():
            self.xml_input.setText(xml_path)
        if xsd_path and Path(xsd_path).exists():
            self.xsd_input.setText(xsd_path)

    def _save_preferences(self) -> None:
        self.settings.setValue("last_xml_path", self.xml_input.text().strip())
        self.settings.setValue("last_xsd_path", self.xsd_input.text().strip())
        self.settings.setValue("auto_validate", self.chk_auto_validate.isChecked())

    def _on_auto_validate_toggled(self, checked: bool) -> None:
        self._save_preferences()
        if checked:
            self._maybe_auto_validate()

    def _has_valid_paths(self) -> bool:
        xml_path = self.xml_input.text().strip()
        xsd_path = self.xsd_input.text().strip()
        return bool(xml_path and xsd_path and Path(xml_path).exists() and Path(xsd_path).exists())

    def _maybe_auto_validate(self) -> None:
        if self.chk_auto_validate.isChecked() and self._has_valid_paths():
            self.run_validation()

    def clear_results(self) -> None:
        self.table.setRowCount(0)
        self.card_total.set_value(0)
        self.card_errors.set_value(0)
        self.card_warnings.set_value(0)

    def run_validation(self) -> None:
        xml_path = self.xml_input.text().strip()
        xsd_path = self.xsd_input.text().strip()

        if not xml_path or not xsd_path:
            QMessageBox.warning(self, "Faltan archivos", "Debes seleccionar XML y XSD.")
            return

        if not Path(xml_path).exists() or not Path(xsd_path).exists():
            QMessageBox.critical(self, "Ruta invalida", "No se encontro el XML o el XSD indicado.")
            return

        try:
            issues = validate(xml_path, xsd_path)
        except RuntimeError as exc:
            message = str(exc)
            if message.startswith("XML mal formado:"):
                line, column = self._extract_line_column_from_error(message)
                self._save_preferences()
                self.load_fatal_error("ERROR", line, column, message)
                return
            QMessageBox.critical(self, "Error de validacion", message)
            return

        self.last_xml_line = self._get_last_line_number(xml_path)
        self._save_preferences()
        self.load_issues(issues)

    def _get_last_line_number(self, xml_path: str) -> int:
        try:
            with open(xml_path, "rb") as file:
                data = file.read()
            if not data:
                return 0
            return data.count(b"\n") + 1
        except OSError:
            return 0

    def _extract_line_column_from_error(self, message: str) -> tuple[int, int]:
        match = re.search(r"line\s+(\d+),\s+column\s+(\d+)", message, flags=re.IGNORECASE)
        if not match:
            return 0, 0
        return int(match.group(1)), int(match.group(2))

    def load_fatal_error(self, level: str, line: int, column: int, message: str) -> None:
        self.table.setRowCount(0)
        self.card_total.set_value(1)
        self.card_errors.set_value(1 if level == "ERROR" else 0)
        self.card_warnings.set_value(1 if level == "AVISO" else 0)

        self.table.insertRow(0)
        level_item = QTableWidgetItem(level)
        line_item = QTableWidgetItem(str(line))
        col_item = QTableWidgetItem(str(column))
        msg_item = QTableWidgetItem(message)

        color = QColor("#ff6b6b") if level == "ERROR" else QColor("#ffcc66")
        brush = QBrush(color)
        for item in (level_item, line_item, col_item, msg_item):
            item.setForeground(brush)
            item.setData(Qt.ItemDataRole.ForegroundRole, brush)

        self.table.setItem(0, 0, level_item)
        self.table.setItem(0, 1, line_item)
        self.table.setItem(0, 2, col_item)
        self.table.setItem(0, 3, msg_item)
        self.table.resizeColumnsToContents()

    def load_issues(self, issues: list[ValidationIssue]) -> None:
        self.table.setRowCount(0)

        errors = [i for i in issues if i.level == "ERROR"]
        warnings = [i for i in issues if i.level == "AVISO"]

        self.card_total.set_value(len(issues))
        self.card_errors.set_value(len(errors))
        self.card_warnings.set_value(len(warnings))

        for issue in issues:
            row = self.table.rowCount()
            self.table.insertRow(row)

            level_item = QTableWidgetItem(issue.level)
            line_item = QTableWidgetItem(str(issue.line))
            col_item = QTableWidgetItem(str(issue.column))
            msg_item = QTableWidgetItem(issue.message)

            if issue.level == "ERROR":
                color = QColor("#ff6b6b")
            else:
                color = QColor("#ffcc66")

            for item in (level_item, line_item, col_item, msg_item):
                item.setForeground(QBrush(color))
                item.setData(Qt.ItemDataRole.ForegroundRole, QBrush(color))

            self.table.setItem(row, 0, level_item)
            self.table.setItem(row, 1, line_item)
            self.table.setItem(row, 2, col_item)
            self.table.setItem(row, 3, msg_item)

        if not issues:
            row = self.table.rowCount()
            self.table.insertRow(row)

            ok_items = (
                QTableWidgetItem("OK"),
                QTableWidgetItem(str(self.last_xml_line)),
                QTableWidgetItem("N/A"),
                QTableWidgetItem("XML valido sin errores ni avisos."),
            )
            ok_brush = QBrush(QColor("#4ade80"))
            for item in ok_items:
                item.setForeground(ok_brush)
                item.setData(Qt.ItemDataRole.ForegroundRole, ok_brush)
                item_font = item.font()
                item_font.setBold(True)
                item.setFont(item_font)

            self.table.setItem(row, 0, ok_items[0])
            self.table.setItem(row, 1, ok_items[1])
            self.table.setItem(row, 2, ok_items[2])
            self.table.setItem(row, 3, ok_items[3])
        self._refresh_message_column()

    def _refresh_message_column(self) -> None:
        h_header = self.table.horizontalHeader()
        if h_header is None:
            return
        h_header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        h_header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        h_header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        h_header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)

    def apply_styles(self) -> None:
        check_icon_rule = ""
        check_icon_path = resource_path("check_white.svg")
        if check_icon_path.exists():
            check_icon_qt_path = check_icon_path.resolve().as_posix()
            check_icon_rule = (
                "\n"
                "            QCheckBox::indicator:checked {\n"
                "                image: url('" + check_icon_qt_path + "');\n"
                "            }\n"
            )

        self.setStyleSheet(
            """
            QWidget {
                background: #1e1e1e;
                color: #d4d4d4;
                font-family: 'Segoe UI';
                font-size: 13px;
            }
            QFrame#TopBar {
                background: #252526;
                border: 1px solid #333333;
                border-radius: 10px;
            }
            QLabel#MainTitle {
                background: transparent;
                color: #ffffff;
                font-size: 28px;
                font-weight: 700;
            }
            QLabel#Subtitle {
                background: transparent;
                color: #9da1a6;
                margin-bottom: 2px;
            }
            QLabel#FieldLabel {
                font-weight: 600;
                color: #c9d1d9;
            }
            QCheckBox {
                color: #d4d4d4;
                spacing: 8px;
                padding: 4px 6px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 1px solid #6a6a6a;
                border-radius: 5px;
                background: #252526;
            }
            QCheckBox::indicator:checked {
                border: 1px solid #1177bb;
                background: #0e639c;
            }
            QCheckBox::indicator:hover {
                border: 1px solid #8a8a8a;
            }
            QLabel#StatusLabel {
                color: #e6edf3;
                background: #252526;
                border: 1px solid #3c3c3c;
                border-radius: 8px;
                padding: 8px 10px;
            }
            QLineEdit {
                background: #252526;
                color: #e6edf3;
                border: 1px solid #3c3c3c;
                border-radius: 8px;
                padding: 8px;
                selection-background-color: #264f78;
                selection-color: #ffffff;
            }
            QLineEdit:focus {
                border: 1px solid #007acc;
            }
            QPushButton {
                background: #0e639c;
                color: #ffffff;
                border: 1px solid #1177bb;
                border-radius: 8px;
                padding: 9px 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #1177bb;
            }
            QPushButton#Secondary {
                background: #3c3c3c;
                color: #e6edf3;
                border: 1px solid #555555;
            }
            QPushButton#Secondary:hover {
                background: #4a4a4a;
            }
            QFrame#StatCard {
                border-radius: 12px;
                border: 1px solid #3c3c3c;
                background: #252526;
            }
            QFrame#StatCard[accent="error"] {
                border-left: 5px solid #f14c4c;
            }
            QFrame#StatCard[accent="warning"] {
                border-left: 5px solid #cca700;
            }
            QFrame#StatCard[accent="neutral"] {
                border-left: 5px solid #569cd6;
            }
            QLabel#CardTitle {
                background: transparent;
                color: #9da1a6;
                font-size: 12px;
            }
            QLabel#CardValue {
                background: transparent;
                font-size: 24px;
                font-weight: 700;
                color: #e6edf3;
            }
            QTableWidget {
                background: #1f1f1f;
                color: #e6edf3;
                alternate-background-color: #252526;
                border: 1px solid #3c3c3c;
                border-radius: 12px;
                gridline-color: #333333;
            }
            QTableWidget::item:hover {
                background: #2a2d2e;
            }
            QTableCornerButton::section {
                background: #252526;
                border: none;
            }
            QHeaderView::section {
                background: #252526;
                color: #d4d4d4;
                border: none;
                border-bottom: 1px solid #3c3c3c;
                padding: 8px;
                font-weight: 700;
            }
            QTableWidget::item {
                background: transparent;
            }
            QTableWidget::item:selected {
                background: #264f78;
                color: #ffffff;
            }
            QScrollBar:vertical {
                background: #1f1f1f;
                width: 12px;
                margin: 8px 2px 8px 2px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #4b4f52;
                min-height: 30px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical:hover {
                background: #5c6166;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: #1f1f1f;
                border-radius: 6px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar:horizontal {
                background: #1f1f1f;
                height: 12px;
                margin: 2px 8px 2px 8px;
                border-radius: 6px;
            }
            QScrollBar::handle:horizontal {
                background: #4b4f52;
                min-width: 30px;
                border-radius: 6px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #5c6166;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: #1f1f1f;
                border-radius: 6px;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
            """
            + check_icon_rule
        )


def main() -> int:
    if not getattr(sys, "frozen", False):
        set_windows_app_id()
    app = QApplication(sys.argv)
    app.setOrganizationName("Rocio")
    app.setApplicationName("Validador XML/XSD")
    app_icon = build_app_icon()
    if not app_icon.isNull():
        app.setWindowIcon(app_icon)

    font = QFont("Segoe UI", 10)
    app.setFont(font)

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())




