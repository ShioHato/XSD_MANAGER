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
        "QCheckBox::indicator:checked {\n"
        f"    image: url('{check_icon_qt_path}');\n"
        "}\n"
    )


def apply_styles(target: QWidget, resource_path: Callable[[str], Path]) -> None:
    style_path = Path(__file__).with_name("styles.qss")
    stylesheet = style_path.read_text(encoding="utf-8")
    stylesheet += _build_check_icon_rule(resource_path)
    target.setStyleSheet(stylesheet)
