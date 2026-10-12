"""Auto Clicker View - Windows 11 Fluent Clicker Suite with Live Theme Sync & Responsive Layout."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QRadioButton, QButtonGroup, QSizePolicy
)
from qfluentwidgets import (
    CardWidget, PrimaryPushButton, PushButton, LineEdit, ComboBox,
    FluentIcon, TitleLabel, SubtitleLabel, BodyLabel, CaptionLabel,
    StrongBodyLabel, SmoothScrollArea, InfoBar, InfoBarPosition,
    qconfig, isDarkTheme
)

from ..components.status_badge import StatusBadge
from ..theme import card_style, hero_card_style, get_text_colors, ThemeTokens


class ClickerView(SmoothScrollArea):
    """Modern Windows 11 Auto Clicker interface with sub-millisecond precision controls."""

    def __init__(self, engine, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.setObjectName("ClickerView")
        self._is_guarded = False

        self.container = QWidget(self)
        self.setWidget(self.container)
        self.setWidgetResizable(True)
        self.setStyleSheet("background-color: transparent; border: none;")

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.layout = QVBoxLayout(self.container)
        self.layout.setContentsMargins(24, 20, 24, 24)
        self.layout.setSpacing(16)

        # Header Title
        title_box = QWidget(self.container)
        title_layout = QVBoxLayout(title_box)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(4)

        self.page_title = TitleLabel("Auto Clicker", title_box)
        self.page_sub = CaptionLabel("High-frequency automated mouse clicker with sub-millisecond spin-wait timing", title_box)
        self.page_sub.setWordWrap(True)

        title_layout.addWidget(self.page_title)
        title_layout.addWidget(self.page_sub)
        self.layout.addWidget(title_box)

        # Primary Control Banner Card
        self.build_control_banner()

        # Timing & Limits Card
        self.build_timing_card()

        # Location & Targeting Card
        self.build_location_card()

        self.layout.addStretch(1)

        # Connect engine signals
        self.engine.signals.state_changed.connect(self.on_state_changed)
        self.engine.signals.clicker_progress.connect(self.on_clicker_progress)
        self.engine.signals.clicker_finished.connect(self.on_clicker_finished)

        # Connect theme sync
        qconfig.themeChanged.connect(self.update_theme)
        self.update_theme()

    def build_control_banner(self) -> None:
        self.banner_card = CardWidget(self.container)
        b_layout = QHBoxLayout(self.banner_card)
        b_layout.setContentsMargins(24, 20, 24, 20)
        b_layout.setSpacing(20)

        # Left Info
        info_col = QWidget(self.banner_card)
        info_col.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        col_layout = QVBoxLayout(info_col)
        col_layout.setContentsMargins(0, 0, 0, 0)
        col_layout.setSpacing(4)

        row1 = QHBoxLayout()
        row1.setSpacing(12)
        self.banner_title = SubtitleLabel("Auto Clicker Engine", info_col)
        self.badge = StatusBadge(info_col)
        row1.addWidget(self.banner_title)
        row1.addWidget(self.badge)
        row1.addStretch(1)

        self.counter_label = CaptionLabel("Ready. Total clicks: 0", info_col)
        self.counter_label.setWordWrap(True)

        col_layout.addLayout(row1)
        col_layout.addWidget(self.counter_label)
        b_layout.addWidget(info_col, 1)

        # Right Trigger Button
        self.toggle_btn = PrimaryPushButton("⚡ Start Auto Clicker", self.banner_card)
        self.toggle_btn.setMinimumSize(180, 44)
        self.toggle_btn.clicked.connect(self.on_toggle_clicked)
        b_layout.addWidget(self.toggle_btn, 0)

        self.layout.addWidget(self.banner_card)

    def build_timing_card(self) -> None:
        self.timing_card = CardWidget(self.container)
        c_layout = QVBoxLayout(self.timing_card)
        c_layout.setContentsMargins(18, 16, 18, 16)
        c_layout.setSpacing(12)

        self.timing_title = StrongBodyLabel("Click Timing & Parameters", self.timing_card)
        c_layout.addWidget(self.timing_title)

        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(8)

        # Row 0: Button Type & Click Interval
        self.lbl_btn = BodyLabel("Mouse Button", self.timing_card)
        self.combo_button = ComboBox(self.timing_card)
        self.combo_button.addItems(["Left", "Right", "Middle"])
        current_btn = str(self.engine.settings.get("click_button", "left")).title()
        self.combo_button.setCurrentText(current_btn if current_btn in ["Left", "Right", "Middle"] else "Left")
        self.combo_button.currentTextChanged.connect(self._save_timing_config)
        grid.addWidget(self.lbl_btn, 0, 0)
        grid.addWidget(self.combo_button, 1, 0)

        self.lbl_interval = BodyLabel("Click Interval (ms)", self.timing_card)
        self.input_interval = LineEdit(self.timing_card)
        self.input_interval.setText(str(self.engine.settings.get("click_interval", "100")))
        self.input_interval.setPlaceholderText("e.g. 100 or 0.1")
        self.input_interval.textChanged.connect(self._save_timing_config)
        grid.addWidget(self.lbl_interval, 0, 1)
        grid.addWidget(self.input_interval, 1, 1)

        # Row 1: Random Jitter & Click Limit
        self.lbl_jitter = BodyLabel("Random Jitter (ms)", self.timing_card)
        self.input_jitter = LineEdit(self.timing_card)
        self.input_jitter.setText(str(self.engine.settings.get("click_jitter", "0")))
        self.input_jitter.setPlaceholderText("e.g. 0 or 5")
        self.input_jitter.textChanged.connect(self._save_timing_config)
        grid.addWidget(self.lbl_jitter, 2, 0)
        grid.addWidget(self.input_jitter, 3, 0)

        self.lbl_limit = BodyLabel("Click Limit (0 = Infinite)", self.timing_card)
        self.input_limit = LineEdit(self.timing_card)
        self.input_limit.setText(str(self.engine.settings.get("click_limit", "0")))
        self.input_limit.setPlaceholderText("0 = until stopped")
        self.input_limit.textChanged.connect(self._save_timing_config)
        grid.addWidget(self.lbl_limit, 2, 1)
        grid.addWidget(self.input_limit, 3, 1)

        c_layout.addLayout(grid)

        self.timing_hint = CaptionLabel(
            "💡 Pro-tip: Interval supports sub-millisecond precision (down to 0.1 ms ~ 10,000 clicks/s). Jitter adds randomized 0..N ms to simulate human variation.",
            self.timing_card
        )
        self.timing_hint.setWordWrap(True)
        c_layout.addWidget(self.timing_hint)

        self.layout.addWidget(self.timing_card)

    def build_location_card(self) -> None:
        self.location_card = CardWidget(self.container)
        c_layout = QVBoxLayout(self.location_card)
        c_layout.setContentsMargins(20, 20, 20, 20)
        c_layout.setSpacing(16)

        self.location_title = StrongBodyLabel("Click Location & Coordinates", self.location_card)
        c_layout.addWidget(self.location_title)

        # Radios
        radio_row = QHBoxLayout()
        radio_row.setSpacing(24)

        self.radio_cursor = QRadioButton("Follow Dynamic Cursor", self.location_card)
        self.radio_fixed = QRadioButton("Fixed Screen Coordinates", self.location_card)

        self.loc_group = QButtonGroup(self.location_card)
        self.loc_group.addButton(self.radio_cursor)
        self.loc_group.addButton(self.radio_fixed)

        is_fixed = self.engine.settings.get("click_location", "cursor") == "fixed"
        self.radio_fixed.setChecked(is_fixed)
        self.radio_cursor.setChecked(not is_fixed)

        self.radio_cursor.toggled.connect(self._on_location_mode_changed)
        self.radio_fixed.toggled.connect(self._on_location_mode_changed)

        radio_row.addWidget(self.radio_cursor)
        radio_row.addWidget(self.radio_fixed)
        radio_row.addStretch(1)
        c_layout.addLayout(radio_row)

        # Coordinate inputs row
        coords_row = QHBoxLayout()
        coords_row.setSpacing(12)

        self.lbl_x = BodyLabel("X:", self.location_card)
        self.input_x = LineEdit(self.location_card)
        self.input_x.setFixedWidth(90)
        self.input_x.setText(str(self.engine.settings.get("fixed_x", "0")))
        self.input_x.textChanged.connect(self._save_location_config)

        self.lbl_y = BodyLabel("Y:", self.location_card)
        self.input_y = LineEdit(self.location_card)
        self.input_y.setFixedWidth(90)
        self.input_y.setText(str(self.engine.settings.get("fixed_y", "0")))
        self.input_y.textChanged.connect(self._save_location_config)

        self.btn_pick_pos = PushButton("📍 Pick Cursor Position", self.location_card, FluentIcon.PIN)
        self.btn_pick_pos.clicked.connect(self.on_pick_position)

        coords_row.addWidget(self.lbl_x)
        coords_row.addWidget(self.input_x)
        coords_row.addWidget(self.lbl_y)
        coords_row.addWidget(self.input_y)
        coords_row.addWidget(self.btn_pick_pos)
        coords_row.addStretch(1)
        c_layout.addLayout(coords_row)

        self.layout.addWidget(self.location_card)

    def update_theme(self) -> None:
        is_dark = isDarkTheme()
        txt = get_text_colors(is_dark)
        c_style = card_style(is_dark)

        # Page Header
        self.page_title.setStyleSheet(f"font-size: 26px; font-weight: 700; color: {txt['primary']};")
        self.page_sub.setStyleSheet(f"font-size: 13px; color: {txt['muted']};")

        # Banner Card
        self.banner_card.setStyleSheet(hero_card_style(is_dark))
        self.banner_title.setStyleSheet(f"font-weight: 600; font-size: 16px; color: {txt['primary']};")
        self.counter_label.setStyleSheet(f"color: {txt['secondary']}; font-size: 13px;")

        # Timing Card
        self.timing_card.setStyleSheet(c_style)
        self.timing_title.setStyleSheet(f"font-size: 15px; color: {txt['primary']}; font-weight: 600;")
        self.lbl_btn.setStyleSheet(f"color: {txt['secondary']}; font-size: 12px;")
        self.lbl_interval.setStyleSheet(f"color: {txt['secondary']}; font-size: 12px;")
        self.lbl_jitter.setStyleSheet(f"color: {txt['secondary']}; font-size: 12px;")
        self.lbl_limit.setStyleSheet(f"color: {txt['secondary']}; font-size: 12px;")
        self.timing_hint.setStyleSheet(f"color: {txt['dim']}; font-size: 11px;")

        # Location Card
        self.location_card.setStyleSheet(c_style)
        self.location_title.setStyleSheet(f"font-size: 15px; color: {txt['primary']}; font-weight: 600;")
        self.radio_cursor.setStyleSheet(f"color: {txt['primary']}; font-size: 13px;")
        self.radio_fixed.setStyleSheet(f"color: {txt['primary']}; font-size: 13px;")
        self.lbl_x.setStyleSheet(f"color: {txt['muted']}; font-weight: bold;")
        self.lbl_y.setStyleSheet(f"color: {txt['muted']}; font-weight: bold;")

    def _save_timing_config(self) -> None:
        self.engine.settings["click_button"] = self.combo_button.currentText().lower()
        self.engine.settings["click_interval"] = self.input_interval.text().strip() or "100"
        self.engine.settings["click_jitter"] = self.input_jitter.text().strip() or "0"
        self.engine.settings["click_limit"] = self.input_limit.text().strip() or "0"
        self.engine.save_settings()

    def _save_location_config(self) -> None:
        self.engine.settings["fixed_x"] = self.input_x.text().strip() or "0"
        self.engine.settings["fixed_y"] = self.input_y.text().strip() or "0"
        self.engine.save_settings()

    def _on_location_mode_changed(self) -> None:
        loc = "fixed" if self.radio_fixed.isChecked() else "cursor"
        self.engine.settings["click_location"] = loc
        self.engine.save_settings()

    def on_pick_position(self) -> None:
        x, y = self.engine.capture_cursor()
        self.input_x.setText(str(x))
        self.input_y.setText(str(y))
        self.radio_fixed.setChecked(True)
        InfoBar.success(
            title="Position Captured",
            content=f"Coordinates locked at X={x}, Y={y}",
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self.window()
        )

    def on_toggle_clicked(self) -> None:
        self._save_timing_config()
        self._save_location_config()
        self.engine.toggle_clicker()

    def set_guarded(self, guarded: bool) -> None:
        """Disable primary execution buttons when viewing Settings tab to avoid accidental conflicts."""
        self._is_guarded = guarded
        if guarded:
            self.toggle_btn.setEnabled(False)
            self.btn_pick_pos.setEnabled(False)
            self.toggle_btn.setToolTip("Execution controls disabled while configuring Settings")
        else:
            self.toggle_btn.setToolTip("")
            self.btn_pick_pos.setEnabled(True)
            self.on_state_changed(self.engine.get_state())

    def on_state_changed(self, state: str) -> None:
        self.badge.set_state(state)
        if self._is_guarded:
            self.toggle_btn.setEnabled(False)
            return

        if state == "CLICKING":
            self.toggle_btn.setEnabled(True)
            self.toggle_btn.setText("⏹ Stop Auto Clicker")
            self.toggle_btn.setStyleSheet("""
                PrimaryPushButton {
                    background-color: #dc2626;
                    color: white;
                    font-size: 14px;
                    font-weight: 700;
                    border-radius: 8px;
                }
                PrimaryPushButton:hover {
                    background-color: #ef4444;
                }
            """)
        else:
            self.toggle_btn.setEnabled(True)
            self.toggle_btn.setText("⚡ Start Auto Clicker")
            self.toggle_btn.setStyleSheet("")

    def on_clicker_progress(self, count: int) -> None:
        self.counter_label.setText(f"Active. Dispatched clicks: {count:,}")

    def on_clicker_finished(self, stopped: bool, count: int) -> None:
        status_text = "Stopped" if stopped else "Finished"
        self.counter_label.setText(f"{status_text}. Total clicks: {count:,}")
