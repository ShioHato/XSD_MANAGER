"""Style helpers for the main UI."""

from pathlib import Path
from typing import Callable
from PyQt6.QtWidgets import QWidget


def _build_check_icon_rule(resource_path: Callable[[str], Path]) -> str:
    check_icon_path = resource_path("check_white.svg")
    if not check_icon_path.exists():
        return ""
    check_icon_qt_path = check_icon_path.resolve().as_posix()
    return (
        "\n"
        "            QCheckBox::indicator:checked {\n"
        f"                image: url('{check_icon_qt_path}');\n"
        "            }\n"
    )


def apply_styles(target: QWidget, resource_path: Callable[[str], Path]) -> None:
    check_icon_rule = _build_check_icon_rule(resource_path)
    target.setStyleSheet(
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
        QLabel#PanelTitle {
            color: #d8dee9;
            font-size: 13px;
            font-weight: 700;
        }
        QWidget#PanelHeader {
            margin: 0px;
            padding: 0px;
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
        QPushButton#PanelOverlayClose {
            color: #9ca3af;
            background: rgba(31, 41, 55, 0.7);
            border: 1px solid rgba(107, 114, 128, 0.35);
            border-radius: 7px;
            padding: 0;
            font-weight: 700;
            font-size: 11px;
            min-width: 14px;
            max-width: 14px;
            min-height: 14px;
            max-height: 14px;
        }
        QPushButton#PanelOverlayClose:hover {
            color: #ffffff;
            background: rgba(31, 41, 55, 0.95);
            border: 1px solid #6b7280;
        }
        QPushButton#PanelOverlayClose:pressed {
            color: #ffffff;
            background: rgba(31, 41, 55, 1.0);
            border: 1px solid #8b939f;
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
            border-left: 5px solid #1a6ad3;
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
