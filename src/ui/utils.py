"""Utility helpers for the desktop UI."""

import sys
from pathlib import Path
import ctypes
from PyQt6.QtGui import QIcon


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

