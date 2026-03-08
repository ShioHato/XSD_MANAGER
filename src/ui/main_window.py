"""Main application window and interaction flows."""

import sys
from pathlib import Path
import ctypes
import re

from PyQt6.QtCore import Qt, QEvent, QSettings
from PyQt6.QtGui import QColor, QBrush, QAction
from PyQt6.QtWidgets import (
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
    QToolBar,
    QHeaderView,
    QSplitter,
    QPlainTextEdit,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

try:
    from src.validar_xml import ValidationIssue, validate
except ImportError:
    from validar_xml import ValidationIssue, validate

from src.ui.styles import apply_styles
from src.ui.utils import build_app_icon, resource_path
from src.ui.widgets import CodeEditor, StatCard


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.settings = QSettings()
        self.last_xml_line = 0
        self._overlay_close_buttons: dict[QWidget, QPushButton] = {}
        self.setWindowTitle("XSD MANAGER")
        self.resize(1240, 760)
        app_icon = build_app_icon()
        if not app_icon.isNull():
            self.setWindowIcon(app_icon)

        self.toolbar = QToolBar("Acciones")
        self.toolbar.setObjectName("TopToolbar")
        self.toolbar.setMovable(False)
        self.toolbar.setFloatable(False)
        self.toolbar.setAllowedAreas(Qt.ToolBarArea.TopToolBarArea)
        central = QWidget()
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(12)
        body = QHBoxLayout()
        body.setSpacing(12)
        root.addLayout(body)

        self._build_toolbar_actions()
        self.main_split = QSplitter(Qt.Orientation.Horizontal)
        self.main_split.setObjectName("MainSplit")
        self.main_split.setHandleWidth(8)
        self.main_split.setChildrenCollapsible(False)
        body.addWidget(self.main_split, 1)

        left_sidebar = self._build_left_sidebar()
        self.main_split.addWidget(left_sidebar)
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
        self._add_overlay_close_button(self.results_box, self._close_validation_panel)
        self.main_vertical_split.addWidget(results_box)
        self.main_vertical_split.setSizes([1, 0])
        self.main_vertical_split.setChildrenCollapsible(False)
        main_layout.addWidget(self.main_vertical_split, 1)

        self.main_split.addWidget(main_content)
        self.main_split.setSizes([260, 1])
        self._refresh_overlay_close_positions()

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

        act_open = QAction("Abrir", self)
        act_open.triggered.connect(self.pick_xsd)
        act_save = QAction("Guardar", self)
        act_save.triggered.connect(self.save_xsd)

        self.toolbar.addAction(act_open)
        self.toolbar.addAction(act_save)

        act_settings = QAction("Ajustes", self)
        act_info = QAction("Info", self)
        act_info.triggered.connect(self.show_info)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.toolbar.addWidget(spacer)

        self.toolbar.addAction(act_settings)
        self.toolbar.addAction(act_info)

    def _build_left_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("LeftSidebar")
        sidebar.setMinimumWidth(220)
        sidebar.setMaximumWidth(520)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        title = QLabel("Herramientas")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        self.xml_input = QLineEdit()
        self.xsd_input = QLineEdit()
        self.xml_input.setPlaceholderText("Selecciona un archivo XML...")
        self.xsd_input.setPlaceholderText("Selecciona un archivo XSD...")
        self.xml_input.setReadOnly(True)
        self.xsd_input.setReadOnly(True)

        self._build_file_row(layout, "XML", self.xml_input, self.pick_xml)
        self._build_file_row(layout, "XSD", self.xsd_input, self.pick_xsd)

        self.validate_toggle_btn = QPushButton("Abrir validador")
        self.validate_toggle_btn.setObjectName("Primary")
        self.validate_toggle_btn.setToolTip("Abrir/Cerrar el panel de validación")
        self.validate_toggle_btn.clicked.connect(self._toggle_validation_panel)
        self._update_validation_toggle_label()
        layout.addWidget(self.validate_toggle_btn)

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

    def _build_panel_header(self, title: str) -> QWidget:
        header = QWidget()
        header.setObjectName("PanelHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(6, 2, 6, 2)
        header_layout.setSpacing(4)

        title_label = QLabel(title)
        title_label.setObjectName("PanelTitle")
        title_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        header_layout.addWidget(title_label)
        header_layout.addStretch(1)

        return header

    def _build_xml_viewer_panel(self) -> QWidget:
        panel = QWidget()
        panel.setObjectName("XmlSidePanel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.setSpacing(8)

        panel_layout.addWidget(self._build_panel_header("Visor y editor XML"))
        self.xml_editor = CodeEditor()
        self.xml_editor.setObjectName("XmlEditor")
        self.xml_editor.setPlaceholderText("Selecciona un XML para mostrar su contenido.")
        self.xml_editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.xml_editor.setReadOnly(False)
        self.xml_editor.setEnabled(False)

        panel_layout.addWidget(self.xml_editor, 1)
        self._add_overlay_close_button(panel, self._close_xml_panel)
        return panel

    def _add_overlay_close_button(self, panel: QWidget, on_close) -> None:
        close_btn = QPushButton("\u00d7", panel)
        close_btn.setObjectName("PanelOverlayClose")
        close_btn.setFixedSize(14, 14)
        close_btn.setToolTip("Cerrar")
        close_btn.clicked.connect(on_close)
        close_btn.hide()
        close_btn.raise_()
        self._overlay_close_buttons[panel] = close_btn
        panel.installEventFilter(self)

    def _refresh_overlay_close_positions(self) -> None:
        for panel in list(self._overlay_close_buttons):
            self._position_overlay_close(panel)

    def _position_overlay_close(self, panel: QWidget) -> None:
        btn = self._overlay_close_buttons.get(panel)
        if btn is None:
            return
        margin = 6
        btn.move(max(0, panel.width() - btn.width() - margin), margin)

    def _set_overlay_close_visible(self, panel: QWidget, visible: bool) -> None:
        btn = self._overlay_close_buttons.get(panel)
        if btn is None:
            return
        btn.setVisible(visible)
        if visible:
            self._position_overlay_close(panel)


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

    def save_xsd(self) -> None:
        path = self.xsd_input.text().strip()
        if not path:
            path, _ = QFileDialog.getSaveFileName(
                self,
                "Guardar XSD",
                "schema.xsd",
                "XSD (*.xsd);;Todos (*.*)",
            )
            if not path:
                return
            self.xsd_input.setText(path)
            self._save_preferences()

        try:
            with open(path, "w", encoding="utf-8") as file:
                file.write(self.xsd_editor.toPlainText())
        except OSError as exc:
            QMessageBox.critical(self, "Error al guardar", str(exc))
            return

        self._save_preferences()
        QMessageBox.information(self, "Guardar XSD", "Archivo guardado correctamente.")

    def show_info(self) -> None:
        QMessageBox.information(
            self,
            "Información",
            "XSD MANAGER\nDiseñado para validar documentos XML contra esquemas XSD.",
        )

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

    def _is_validation_panel_visible(self) -> bool:
        if not hasattr(self, "results_box"):
            return False
        if not self.results_box.isVisible():
            return False
        if hasattr(self, "main_vertical_split"):
            sizes = self.main_vertical_split.sizes()
            if len(sizes) > 1 and sizes[1] <= 0:
                return False
        return True

    def _set_validation_panel_visible(self, visible: bool) -> None:
        if not hasattr(self, "main_vertical_split") or not hasattr(self, "results_box"):
            return
        if visible:
            self.main_vertical_split.setSizes([3, 1])
            self.results_box.setVisible(True)
        else:
            self.main_vertical_split.setSizes([1, 0])
            self.results_box.setVisible(False)
        self._update_validation_toggle_label()

    def _toggle_validation_panel(self) -> None:
        if not self._is_validation_panel_visible():
            if not self._has_valid_paths():
                QMessageBox.warning(self, "Faltan archivos", "Debes seleccionar XML y XSD.")
                return
            self._set_validation_panel_visible(True)
            self.run_validation()
            return

        self._set_validation_panel_visible(False)

    def _close_validation_panel(self) -> None:
        self._set_validation_panel_visible(False)

    def _update_validation_toggle_label(self) -> None:
        if not hasattr(self, "validate_toggle_btn"):
            return
        self.validate_toggle_btn.setText(
            "Ocultar validador" if self._is_validation_panel_visible() else "Abrir validador"
        )

    def _close_xml_panel(self) -> None:
        self.xml_view_panel.setVisible(False)
        if hasattr(self, "editor_split"):
            self.editor_split.setSizes([1, 0])

    def eventFilter(self, watched, event):  # type: ignore[override]
        if watched in self._overlay_close_buttons:
            if event.type() == QEvent.Type.Enter:
                self._set_overlay_close_visible(watched, True)
            elif event.type() == QEvent.Type.Leave:
                self._set_overlay_close_visible(watched, False)
            elif event.type() == QEvent.Type.Resize:
                if self._overlay_close_buttons.get(watched) and self._overlay_close_buttons[watched].isVisible():
                    self._position_overlay_close(watched)
        return super().eventFilter(watched, event)

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
        self._set_validation_panel_visible(True)
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
        self._set_validation_panel_visible(True)
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
        apply_styles(self, resource_path)



