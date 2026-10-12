"""Macro Plus - Windows 11 Fluent Macro Recorder, Precision Player & Auto Clicker.

Run with ``python macro_plus.py``. Recordings are portable JSON documents saved
in the ``recordings`` directory.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure package directory is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QDir, QSize, QResource

from macro_engine import MacroEngine
from ui.app_window import MacroPlusWindow


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("Macro Plus")
    app.setOrganizationName("Macro Plus Precision Suite")

    engine = MacroEngine()
    window = MacroPlusWindow(engine)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
