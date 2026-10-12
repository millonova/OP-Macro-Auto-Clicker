"""Interactive Hotkey Configuration Row Component with Dynamic Theme Support & Responsive Layout."""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QSizePolicy
from qfluentwidgets import (
    CardWidget, ToolButton, FluentIcon, BodyLabel, CaptionLabel,
    qconfig, isDarkTheme
)

from ..theme import card_style, key_badge_style, capture_button_style, get_text_colors


class HotkeyRowCard(CardWidget):
    """Windows 11 Settings-style card row for binding a global hotkey with live capture."""

    capture_requested = pyqtSignal(str)  # action_name

    def __init__(self, action_name: str, title: str, description: str, current_hotkey: str, parent=None):
        super().__init__(parent)
        self.action_name = action_name
        self._current_hotkey = current_hotkey
        self._is_capturing = False

        self.setMinimumHeight(64)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(16)

        # Left Info Text
        text_container = QWidget(self)
        text_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        text_layout = QVBoxLayout(text_container)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)

        self.title_label = BodyLabel(title, text_container)
        self.title_label.setWordWrap(True)
        self.desc_label = CaptionLabel(description, text_container)
        self.desc_label.setWordWrap(True)

        text_layout.addWidget(self.title_label)
        text_layout.addWidget(self.desc_label)
        layout.addWidget(text_container, 1)

        # Right Controls: Key badge & Icon-only Capture Button
        controls_box = QWidget(self)
        controls_layout = QHBoxLayout(controls_box)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(10)

        self.key_badge = QLabel(current_hotkey, controls_box)
        self.key_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.key_badge.setMinimumWidth(64)
        self.key_badge.setFixedHeight(32)

        self.capture_btn = ToolButton(FluentIcon.EDIT, controls_box)
        self.capture_btn.setFixedSize(32, 32)
        self.capture_btn.setToolTip("Edit keybinding")
        self.capture_btn.clicked.connect(self._on_capture_clicked)

        controls_layout.addWidget(self.key_badge)
        controls_layout.addWidget(self.capture_btn)
        layout.addWidget(controls_box, 0)

        # Hook theme change
        qconfig.themeChanged.connect(self.update_theme)
        self.update_theme()

    def update_theme(self) -> None:
        is_dark = isDarkTheme()
        txt = get_text_colors(is_dark)

        self.setStyleSheet(card_style(is_dark))
        self.title_label.setStyleSheet(f"font-weight: 600; font-size: 13px; color: {txt['primary']};")
        self.desc_label.setStyleSheet(f"color: {txt['muted']}; font-size: 11px;")
        self.key_badge.setStyleSheet(key_badge_style(is_dark, self._is_capturing))
        self.capture_btn.setStyleSheet(capture_button_style(is_dark, self._is_capturing))

    def update_key_badge(self, hotkey_text: str) -> None:
        self._current_hotkey = hotkey_text
        self.key_badge.setText(hotkey_text)
        self.key_badge.setStyleSheet(key_badge_style(isDarkTheme(), self._is_capturing))

    def set_capturing(self, capturing: bool) -> None:
        self._is_capturing = capturing
        is_dark = isDarkTheme()
        if capturing:
            self.capture_btn.setIcon(FluentIcon.SYNC)
            self.capture_btn.setToolTip("Listening... Press key combination (Esc to cancel)")
            self.key_badge.setText("Press Keys (Esc to cancel)")
        else:
            self.capture_btn.setIcon(FluentIcon.EDIT)
            self.capture_btn.setToolTip("Edit keybinding")
            self.key_badge.setText(self._current_hotkey)

        self.key_badge.setStyleSheet(key_badge_style(is_dark, capturing))
        self.capture_btn.setStyleSheet(capture_button_style(is_dark, capturing))

    def show_conflict(self, hotkey_text: str) -> None:
        """Visual alert on duplicate hotkey while keeping capture armed for immediate recapture."""
        self._is_capturing = True
        self.key_badge.setText(f"In Use: {hotkey_text} (Press new key)")
        self.key_badge.setStyleSheet("""
            QLabel {
                background-color: rgba(239, 68, 68, 0.15);
                border: 1px dashed #ef4444;
                border-radius: 6px;
                padding: 4px 10px;
                font-family: 'Segoe UI', 'Consolas', sans-serif;
                font-weight: 700;
                font-size: 11px;
                color: #ef4444;
            }
        """)
        self.capture_btn.setIcon(FluentIcon.SYNC)
        self.capture_btn.setToolTip("Key conflict! Press a different key combination (Esc to cancel)")
        self.capture_btn.setStyleSheet(capture_button_style(isDarkTheme(), True))

    def _on_capture_clicked(self) -> None:
        self.capture_requested.emit(self.action_name)
