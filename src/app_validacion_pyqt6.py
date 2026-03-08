import sys
from pathlib import Path
import ctypes
import re
from typing import cast
from PyQt6.QtCore import Qt, QSettings, QRect, QSize
from PyQt6.QtGui import QColor, QFont, QIcon, QBrush, QPainter, QTextFormat
from PyQt6.QtGui import QAction
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
    QTextEdit,
    QToolBar,
    QHeaderView,
    QListWidget,
    QSplitter,
    QPlainTextEdit,
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


class LineNumberArea(QWidget):
    def __init__(self, editor: "CodeEditor") -> None:
        super().__init__(editor)
        self.code_editor = editor
        self.setObjectName("LineNumberArea")

    def sizeHint(self) -> QSize:  # type: ignore[override]
        return QSize(self.code_editor.line_number_area_width(), 0)

    def paintEvent(self, event) -> None:  # type: ignore[override]
        self.code_editor.line_number_area_paint_event(event)


class CodeEditor(QPlainTextEdit):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.line_number_area = LineNumberArea(self)
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)

        self.update_line_number_area_width(0)
        self.highlight_current_line()

    def line_number_area_width(self) -> int:
        digits = len(str(max(1, self.blockCount())))
        return 10 + self.fontMetrics().horizontalAdvance("0") * digits + 8

    def update_line_number_area_width(self, _=0) -> None:
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)
        self.line_number_area.update()

    def update_line_number_area(self, rect: QRect | None, dy: int) -> None:
        if rect is None:
            self.line_number_area.update()
            return

        safe_rect = cast(QRect, rect)
        viewport = self.viewport()
        if viewport is None:
            self.line_number_area.update()
            return
        viewport_rect = viewport.rect()

        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(
                0,
                safe_rect.y(),
                self.line_number_area_width(),
                safe_rect.height(),
            )
        if safe_rect.contains(viewport_rect):
            self.update_line_number_area_width()

    def line_number_area_paint_event(self, event) -> None:
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor("#0d0d0d"))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible():
                line = str(block_number + 1)
                if block_number == self.textCursor().blockNumber():
                    painter.fillRect(
                        0,
                        top,
                        self.line_number_area.width(),
                        self.fontMetrics().height(),
                        QColor("#2a2a2a"),
                    )
                    painter.setPen(QColor("#d4d4d4"))
                else:
                    painter.setPen(QColor("#7f7f7f"))

                if bottom >= event.rect().top():
                    painter.drawText(
                        0,
                        top,
                        self.line_number_area.width() - 6,
                        self.fontMetrics().height(),
                        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                        line,
                    )

            block = block.next()
            block_number += 1
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))

    def highlight_current_line(self) -> None:
        extra_selections = []
        selection = QTextEdit.ExtraSelection()
        selection.format.setBackground(QColor("#0b1f32"))
        selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
        selection.cursor = self.textCursor()
        selection.cursor.clearSelection()
        extra_selections.append(selection)
        self.setExtraSelections(extra_selections)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.settings = QSettings()
        self.last_xml_line = 0
        self.setWindowTitle("XSD MANAGER")
        self.resize(1240, 760)
        app_icon = build_app_icon()
        if not app_icon.isNull():
            self.setWindowIcon(app_icon)

        self.toolbar = QToolBar("Acciones")
        self.toolbar.setObjectName("TopToolbar")
        central = QWidget()
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(12)
        body = QHBoxLayout()
        body.setSpacing(12)
        root.addLayout(body)

        self._build_toolbar_actions()
        left_sidebar = self._build_left_sidebar()
        body.addWidget(left_sidebar)

        self.main_split = QSplitter(Qt.Orientation.Horizontal)
        self.main_split.setObjectName("MainSplit")
        self.main_split.setHandleWidth(8)
        self.main_split.setChildrenCollapsible(False)
        body.addWidget(self.main_split, 1)
        body.setStretch(1, 1)

        main_content = QWidget()
        main_layout = QVBoxLayout(main_content)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(12)

        self.main_vertical_split = QSplitter(Qt.Orientation.Vertical)
        self.main_vertical_split.setObjectName("MainVerticalSplit")
        self.main_vertical_split.setHandleWidth(8)
        self.main_vertical_split.setChildrenCollapsible(False)
        dual_editor_card = QFrame()
        dual_editor_card.setObjectName("DualEditorCard")

        dual_editor_layout = QHBoxLayout(dual_editor_card)
        dual_editor_layout.setContentsMargins(12, 10, 12, 10)
        dual_editor_layout.setSpacing(10)

        self.editor_split = QSplitter(Qt.Orientation.Horizontal)
        self.editor_split.setObjectName("EditorSplit")
        self.editor_split.setHandleWidth(8)
        self.editor_split.setChildrenCollapsible(False)

        xsd_view_frame = QFrame()
        xsd_view_frame.setObjectName("EditorPanel")
        xsd_view_layout = QVBoxLayout(xsd_view_frame)
        xsd_view_layout.setContentsMargins(0, 0, 0, 0)
        xsd_view_layout.setSpacing(8)

        xsd_view_title = QLabel("XSD")
        xsd_view_title.setObjectName("SectionTitle")
        self.xsd_editor = CodeEditor()
        self.xsd_editor.setObjectName("XsdEditor")
        self.xsd_editor.setPlaceholderText("Selecciona un XSD para visualizar su contenido.")
        self.xsd_editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.xsd_editor.setReadOnly(False)
        xsd_view_layout.addWidget(xsd_view_title)
        xsd_view_layout.addWidget(self.xsd_editor, 1)

        self.xml_view_panel = self._build_xml_viewer_panel()
        self.editor_split.addWidget(xsd_view_frame)
        self.editor_split.addWidget(self.xml_view_panel)
        self.editor_split.setSizes([1, 0 if not self.xml_view_panel.isVisible() else 1])
        self.editor_split.setChildrenCollapsible(False)
        dual_editor_layout.addWidget(self.editor_split, 1)
        self.main_vertical_split.addWidget(dual_editor_card)

        results_box = QFrame()
        results_box.setObjectName("EditorCard")
        results_layout = QVBoxLayout(results_box)
        results_layout.setContentsMargins(0, 0, 0, 0)
        results_layout.setSpacing(8)

        cards = QGridLayout()
        cards.setHorizontalSpacing(10)
        cards.setVerticalSpacing(10)

        self.card_total = StatCard("Incidencias", "neutral")
        self.card_errors = StatCard("Errores", "error")
        self.card_warnings = StatCard("Avisos", "warning")

        cards.addWidget(self.card_total, 0, 0)
        cards.addWidget(self.card_errors, 0, 1)
        cards.addWidget(self.card_warnings, 0, 2)
        results_layout.addLayout(cards)

        self.status = QLabel("Esperando acción de validación...")
        self.status.setObjectName("StatusLabel")
        self.status.hide()
        results_layout.addWidget(self.status)

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
        results_layout.addWidget(self.table, 1)
        results_box.setVisible(False)
        self.results_box = results_box
        self.main_vertical_split.addWidget(results_box)
        self.main_vertical_split.setSizes([1, 0])
        self.main_vertical_split.setChildrenCollapsible(False)
        main_layout.addWidget(self.main_vertical_split, 1)

        self.main_split.addWidget(main_content)
        self.main_split.setSizes([260, 1])

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

    def _build_toolbar_actions(self) -> None:
        if not hasattr(self, "toolbar"):
            return
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolbar)
        self.toolbar.clear()

        act_open_xml = QAction("Abrir XML", self)
        act_open_xml.triggered.connect(self.pick_xml)
        act_open_xsd = QAction("Abrir XSD", self)
        act_open_xsd.triggered.connect(self.pick_xsd)
        act_validate = QAction("Validar", self)
        act_validate.triggered.connect(self.run_validation)
        act_clear = QAction("Limpiar", self)
        act_clear.triggered.connect(self.clear_results)
        act_dummy = QAction("Ajustes", self)
        act_dummy.setEnabled(False)

        self.toolbar.addAction(act_open_xml)
        self.toolbar.addAction(act_open_xsd)
        self.toolbar.addSeparator()
        self.toolbar.addAction(act_validate)
        self.toolbar.addAction(act_clear)
        self.toolbar.addSeparator()
        self.toolbar.addAction(act_dummy)

    def _build_left_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("LeftSidebar")
        sidebar.setMinimumWidth(220)
        sidebar.setMaximumWidth(260)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        title = QLabel("Herramientas")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        nav = QListWidget()
        nav.addItems(["Visión general", "Validador XSD", "Historial", "Proyectos", "Ajustes"])
        nav.setObjectName("NavList")
        layout.addWidget(nav)

        self.xml_input = QLineEdit()
        self.xsd_input = QLineEdit()
        self.xml_input.setPlaceholderText("Selecciona un archivo XML...")
        self.xsd_input.setPlaceholderText("Selecciona un archivo XSD...")
        self.xml_input.setReadOnly(True)
        self.xsd_input.setReadOnly(True)

        self._build_file_row(layout, "XML", self.xml_input, self.pick_xml)
        self._build_file_row(layout, "XSD", self.xsd_input, self.pick_xsd)

        validate_btn = QPushButton("Validar XSD + XML")
        validate_btn.setObjectName("Primary")
        validate_btn.clicked.connect(self.run_validation)
        layout.addWidget(validate_btn)

        self.chk_auto_validate = QCheckBox("Validación automática")
        self.chk_auto_validate.setChecked(False)
        self.chk_auto_validate.toggled.connect(self._on_auto_validate_toggled)
        self.chk_auto_validate.hide()
        layout.addWidget(self.chk_auto_validate)

        dummy = QLabel("Panel lateral de utilidades")
        dummy.setObjectName("SidebarHint")
        layout.addWidget(dummy)
        layout.addStretch(1)
        return sidebar

    def _build_xml_viewer_panel(self) -> QWidget:
        panel = QWidget()
        panel.setObjectName("XmlSidePanel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.setSpacing(8)

        xml_view_title = QLabel("Visor y editor XML")
        xml_view_title.setObjectName("SectionTitle")
        self.xml_editor = CodeEditor()
        self.xml_editor.setObjectName("XmlEditor")
        self.xml_editor.setPlaceholderText("Selecciona un XML para mostrar su contenido.")
        self.xml_editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.xml_editor.setReadOnly(False)
        self.xml_editor.setEnabled(False)

        panel_layout.addWidget(xml_view_title)
        panel_layout.addWidget(self.xml_editor, 1)
        return panel

    def _build_file_row(self, parent_layout: QVBoxLayout | QHBoxLayout, label_text: str, line_edit: QLineEdit, pick_fn) -> None:
        row = QHBoxLayout()
        row.setSpacing(8)

        label = QLabel(label_text)
        label.setObjectName("FieldLabel")
        label.setMinimumWidth(40)

        button = QPushButton("Examinar")
        button.setObjectName("Primary")
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
            self._load_xml_into_editor(path)
            self._maybe_auto_validate()

    def pick_xsd(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Seleccionar XSD", "", "XSD (*.xsd);;Todos (*.*)")
        if path:
            self.xsd_input.setText(path)
            self._save_preferences()
            self._load_xsd_into_editor(path)
            self._maybe_auto_validate()

    def _load_last_paths(self) -> None:
        xml_path = self.settings.value("last_xml_path", "", str)
        xsd_path = self.settings.value("last_xsd_path", "", str)
        self.chk_auto_validate.setChecked(False)

        if xml_path and Path(xml_path).exists():
            self.xml_input.setText(xml_path)
        if xsd_path and Path(xsd_path).exists():
            self.xsd_input.setText(xsd_path)
        self._load_xsd_into_editor(xsd_path)
        self._load_xml_into_editor(xml_path)

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

    def _load_xml_into_editor(self, xml_path: str) -> None:
        if not xml_path or not Path(xml_path).exists():
            self.xml_editor.setPlainText("")
            self.xml_editor.setEnabled(False)
            self.xml_view_panel.setVisible(False)
            if hasattr(self, "editor_split"):
                self.editor_split.setSizes([1, 0])
            return

        try:
            with open(xml_path, "r", encoding="utf-8", errors="replace") as file:
                content = file.read()
        except OSError:
            content = ""
        self.xml_editor.setPlainText(content)
        self.xml_editor.setEnabled(True)
        self.xml_view_panel.setVisible(True)
        if hasattr(self, "editor_split"):
            current_sizes = self.editor_split.sizes()
            if not current_sizes or current_sizes[1] == 0:
                self.editor_split.setSizes([3, 1])

    def _load_xsd_into_editor(self, xsd_path: str) -> None:
        if not xsd_path or not Path(xsd_path).exists():
            self.xsd_editor.setPlainText("")
            self.xsd_editor.setEnabled(False)
            return

        try:
            with open(xsd_path, "r", encoding="utf-8", errors="replace") as file:
                content = file.read()
        except OSError:
            content = ""
        self.xsd_editor.setPlainText(content)
        self.xsd_editor.setEnabled(True)

    def clear_results(self) -> None:
        self.table.setRowCount(0)
        self.card_total.set_value(0)
        self.card_errors.set_value(0)
        self.card_warnings.set_value(0)
        self.results_box.setVisible(False)
        self.status.hide()
        if hasattr(self, "main_vertical_split"):
            self.main_vertical_split.setSizes([1, 0])

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
        if hasattr(self, "main_vertical_split"):
            self.main_vertical_split.setSizes([3, 1])
        self.results_box.setVisible(True)
        self.load_issues(issues)
        self.status.setText("Validación completada.")
        self.status.show()

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
        self.results_box.setVisible(True)
        if hasattr(self, "main_vertical_split"):
            self.main_vertical_split.setSizes([3, 1])
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
        self.results_box.setVisible(True)
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
                background: #101010;
                color: #d4d4d4;
                font-family: 'Segoe UI';
                font-size: 13px;
            }
            QMainWindow::separator {
                background: #2e2e2e;
                width: 1px;
                height: 1px;
            }
            QToolBar#TopToolbar {
                background: #252526;
                border: 1px solid #333333;
                border-radius: 8px;
                padding: 6px;
                spacing: 6px;
            }
            QToolBar#TopToolbar QToolButton {
                background: #333333;
                color: #e5e7eb;
                border-radius: 6px;
                padding: 8px 10px;
                margin-right: 2px;
            }
            QToolBar#TopToolbar QToolButton:hover {
                background: #3f3f3f;
                color: #ffffff;
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
            QFrame#LeftSidebar {
                border: 1px solid #3a3a3a;
                border-radius: 12px;
                background: #1e1e1e;
            }
            QListWidget#NavList {
                background: #1b1b1b;
                border: 1px solid #3a3a3a;
                border-radius: 10px;
                color: #e5e7eb;
                padding: 4px;
            }
            QLabel#SectionTitle {
                color: #e5e5e5;
                font-size: 15px;
                font-weight: 700;
            }
            QLabel#SidebarHint {
                background: #1a1a1a;
                border: 1px dashed #3a3a3a;
                border-radius: 8px;
                padding: 10px;
                color: #9ca3af;
                min-height: 54px;
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
                border: 1px solid #555555;
                border-radius: 5px;
                background: #2b2b2b;
            }
            QCheckBox::indicator:checked {
                border: 1px solid #5a5a5a;
                background: #3d3d3d;
            }
            QCheckBox::indicator:hover {
                border: 1px solid #707070;
            }
            QLabel#StatusLabel {
                color: #e6edf3;
                background: #1f1f1f;
                border: 1px solid #3a3a3a;
                border-radius: 8px;
                padding: 8px 10px;
            }
            QLineEdit {
                background: #1f1f1f;
                color: #e6edf3;
                border: 1px solid #3a3a3a;
                border-radius: 8px;
                padding: 8px;
                selection-background-color: #4a4a4a;
                selection-color: #ffffff;
            }
            QLineEdit:focus {
                border: 1px solid #606060;
            }
            QPushButton {
                background: #3a3a3a;
                color: #ffffff;
                border: 1px solid #5a5a5a;
                border-radius: 8px;
                padding: 9px 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #4a4a4a;
            }
            QPushButton#Secondary {
                background: #303030;
                color: #e6edf3;
                border: 1px solid #505050;
            }
            QPushButton#Secondary:hover {
                background: #3f3f3f;
            }
            QPushButton#Primary {
                background: #0f60d6;
                color: #ffffff;
                border: 1px solid #2f7edb;
            }
            QPushButton#Primary:hover {
                background: #1a6ad3;
            }
            QFrame#EditorCard {
                background: #202020;
                border: 1px solid #3a3a3a;
                border-radius: 12px;
            }
            QFrame#DualEditorCard {
                background: #202020;
                border: 1px solid #3a3a3a;
                border-radius: 12px;
            }
            QFrame#EditorPanel, QWidget#XmlSidePanel {
                background: #151515;
                border: 1px solid #2d2d2d;
                border-radius: 10px;
            }
            QPlainTextEdit#XsdEditor {
                background: #111111;
                color: #e2e8f0;
                border: 1px solid #2d2d2d;
                border-radius: 10px;
                font-family: 'Consolas', 'Cascadia Code', 'Courier New', monospace;
                font-size: 12px;
                padding: 10px;
                selection-background-color: #3a3a3a;
                selection-color: #ffffff;
            }
            QPlainTextEdit#XmlEditor {
                background: #111111;
                color: #e2e8f0;
                border: 1px solid #2d2d2d;
                border-radius: 10px;
                font-family: 'Consolas', 'Cascadia Code', 'Courier New', monospace;
                font-size: 12px;
                padding: 10px;
                selection-background-color: #3a3a3a;
                selection-color: #ffffff;
            }
            QWidget#LineNumberArea {
                background: #0d0d0d;
            }
            QSplitter#MainSplit::handle {
                background: #3a3a3a;
                width: 8px;
                border-radius: 4px;
            }
            QSplitter#MainSplit::handle:horizontal,
            QSplitter#MainVerticalSplit::handle:vertical,
            QSplitter#EditorSplit::handle:horizontal {
                background: #3a3a3a;
                width: 8px;
                height: 8px;
                border-radius: 4px;
            }
            QSplitter#MainSplit::handle:hover,
            QSplitter#MainVerticalSplit::handle:hover,
            QSplitter#EditorSplit::handle:hover {
                background: #666666;
            }
            QFrame#StatCard {
                border-radius: 12px;
                border: 1px solid #3c3c3c;
                background: #1b1b1b;
            }
            QFrame#StatCard[accent="error"] {
                border-left: 5px solid #f14c4c;
            }
            QFrame#StatCard[accent="warning"] {
                border-left: 5px solid #cca700;
            }
            QFrame#StatCard[accent="neutral"] {
                border-left: 5px solid #3a3a3a;
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
                background: #3a3a3a;
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


