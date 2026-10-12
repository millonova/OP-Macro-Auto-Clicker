"""Status Badge Component with Modern Fluent Aesthetics and Live Theme Synchronization."""

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor, QPainter, QBrush
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from qfluentwidgets import qconfig, isDarkTheme

from ..theme import status_badge_config


class StatusBadge(QWidget):
    """Modern glowing status badge for displaying engine operational states."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_state = "IDLE"
        self.setMinimumHeight(32)
        self.setFixedHeight(34)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 4, 14, 4)
        layout.setSpacing(8)

        self.dot_widget = DotWidget(self)
        self.text_label = QLabel("IDLE", self)
        self.text_label.setStyleSheet("font-size: 11px; font-weight: 700; letter-spacing: 0.5px;")

        layout.addWidget(self.dot_widget)
        layout.addWidget(self.text_label)

        # Hook theme change
        qconfig.themeChanged.connect(self.update_theme)
        self.set_state("IDLE")

    def set_state(self, state: str) -> None:
        self._current_state = state.upper()
        self.update_theme()

    def update_theme(self) -> None:
        cfg = status_badge_config(self._current_state, isDarkTheme())
        self.text_label.setText(str(cfg["label"]))
        self.text_label.setStyleSheet(
            f"color: {cfg['text_color']}; font-size: 11px; font-weight: 700; background: transparent; letter-spacing: 0.5px;"
        )
        self.dot_widget.set_color(str(cfg["dot_color"]))
        self.setStyleSheet(
            f"""
            StatusBadge {{
                background-color: {cfg['bg']};
                border: 1px solid {cfg['border']};
                border-radius: 16px;
            }}
            """
        )
        self.update()


class DotWidget(QWidget):
    """Small circle drawing widget for status indicator."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._color = QColor("#94a3b8")
        self.setFixedSize(10, 10)

    def set_color(self, hex_color: str) -> None:
        self._color = QColor(hex_color)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(self._color))
        painter.drawEllipse(1, 1, 8, 8)
