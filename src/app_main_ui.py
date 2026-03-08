import sys

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QApplication

from src.ui.main_window import MainWindow
from src.ui.utils import build_app_icon, set_windows_app_id


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

