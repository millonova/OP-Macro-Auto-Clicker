"""Dashboard View - Windows 11 Fluent Overview & Quick Actions with Dynamic Theming and Responsive Layout."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QSizePolicy
)
from qfluentwidgets import (
    CardWidget, PrimaryPushButton, PushButton,
    FluentIcon, TitleLabel, SubtitleLabel, BodyLabel, CaptionLabel,
    StrongBodyLabel, SmoothScrollArea, qconfig, isDarkTheme
)

from ..components.status_badge import StatusBadge
from ..theme import (
    card_style, hero_card_style, panic_hero_button_style,
    get_text_colors, ThemeTokens
)


class DashboardView(SmoothScrollArea):
    """Modern Dashboard overview providing instant status, quick triggers, and operational telemetry."""

    BREAKPOINT_WIDE = 820

    def __init__(self, engine, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.setObjectName("DashboardView")
        self._is_wide_layout = True
        self._is_guarded = False

        self.container = QWidget(self)
        self.setWidget(self.container)
        self.setWidgetResizable(True)
        self.setStyleSheet("background-color: transparent; border: none;")

        # Prevent horizontal clipping and geometry distortion
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.layout = QVBoxLayout(self.container)
        self.layout.setContentsMargins(24, 20, 24, 24)
        self.layout.setSpacing(16)

        # Header Title Box
        title_box = QWidget(self.container)
        title_layout = QVBoxLayout(title_box)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(4)

        self.page_title = TitleLabel("Macro Plus Dashboard", title_box)
        self.page_sub = CaptionLabel("High-precision macro recording, deterministic playback & ultra-fast auto-clicking", title_box)
        self.page_sub.setWordWrap(True)

        title_layout.addWidget(self.page_title)
        title_layout.addWidget(self.page_sub)
        self.layout.addWidget(title_box)

        # Hero Status Card
        self.build_hero_card()

        # Quick Actions Section
        self.build_quick_actions()

        # Telemetry & Status Cards
        self.build_telemetry_grid()

        self.layout.addStretch(1)

        # Connect engine signals
        self.engine.signals.state_changed.connect(self.on_state_changed)
        self.engine.signals.actions_updated.connect(self.on_actions_updated)
        self.engine.signals.clicker_progress.connect(self.on_clicker_progress)
        self.engine.signals.clicker_finished.connect(self.on_clicker_finished)

        # Connect theme sync
        qconfig.themeChanged.connect(self.update_theme)
        self.update_theme()

    def build_hero_card(self) -> None:
        self.hero_card = CardWidget(self.container)
        hero_layout = QHBoxLayout(self.hero_card)
        hero_layout.setContentsMargins(20, 16, 20, 16)
        hero_layout.setSpacing(16)

        # Left: State & Info
        info_widget = QWidget(self.hero_card)
        info_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        info_layout = QVBoxLayout(info_widget)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(4)

        header_row = QHBoxLayout()
        header_row.setSpacing(10)

        self.system_status_label = SubtitleLabel("System Status", info_widget)
        self.status_badge = StatusBadge(info_widget)

        header_row.addWidget(self.system_status_label)
        header_row.addWidget(self.status_badge)
        header_row.addStretch(1)

        self.status_desc_label = CaptionLabel(
            "Engine is idle and ready. Press a global hotkey or click a trigger button below to begin.", info_widget
        )
        self.status_desc_label.setWordWrap(True)

        info_layout.addLayout(header_row)
        info_layout.addWidget(self.status_desc_label)
        hero_layout.addWidget(info_widget, 1)

        # Right: Panic Stop Quick Button
        self.panic_hero_btn = PushButton("🛑 Panic Stop", self.hero_card)
        self.panic_hero_btn.setMinimumSize(110, 36)
        self.panic_hero_btn.clicked.connect(self.engine.stop_all)
        hero_layout.addWidget(self.panic_hero_btn, 0)

        self.layout.addWidget(self.hero_card)

    def build_quick_actions(self) -> None:
        self.actions_box = QWidget(self.container)
        actions_layout = QVBoxLayout(self.actions_box)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(8)

        self.triggers_heading = StrongBodyLabel("Quick Triggers", self.actions_box)
        actions_layout.addWidget(self.triggers_heading)

        self.triggers_grid_container = QWidget(self.actions_box)
        self.triggers_grid = QGridLayout(self.triggers_grid_container)
        self.triggers_grid.setContentsMargins(0, 0, 0, 0)
        self.triggers_grid.setSpacing(12)

        # 1. Record Trigger Card
        self.record_card = CardWidget(self.triggers_grid_container)
        r_layout = QVBoxLayout(self.record_card)
        r_layout.setContentsMargins(14, 14, 14, 14)
        r_layout.setSpacing(8)
        self.r_title = StrongBodyLabel("Macro Recorder", self.record_card)
        self.r_desc = CaptionLabel("Record mouse clicks, moves, and keystrokes.", self.record_card)
        self.r_desc.setWordWrap(True)
        self.btn_record = PrimaryPushButton("⏺ Record", self.record_card, FluentIcon.VIDEO)
        self.btn_record.clicked.connect(self.engine.toggle_recording)
        r_layout.addWidget(self.r_title)
        r_layout.addWidget(self.r_desc)
        r_layout.addWidget(self.btn_record)

        # 2. Playback Trigger Card
        self.play_card = CardWidget(self.triggers_grid_container)
        p_layout = QVBoxLayout(self.play_card)
        p_layout.setContentsMargins(14, 14, 14, 14)
        p_layout.setSpacing(8)
        self.p_title = StrongBodyLabel("Macro Playback", self.play_card)
        self.p_desc = CaptionLabel("Replay recorded actions with 1ms precision.", self.play_card)
        self.p_desc.setWordWrap(True)
        self.btn_play = PrimaryPushButton("▶ Play", self.play_card, FluentIcon.PLAY)
        self.btn_play.clicked.connect(self.engine.toggle_playback)
        p_layout.addWidget(self.p_title)
        p_layout.addWidget(self.p_desc)
        p_layout.addWidget(self.btn_play)

        # 3. Auto Clicker Trigger Card
        self.clicker_card = CardWidget(self.triggers_grid_container)
        c_layout = QVBoxLayout(self.clicker_card)
        c_layout.setContentsMargins(14, 14, 14, 14)
        c_layout.setSpacing(8)
        self.c_title = StrongBodyLabel("Auto Clicker", self.clicker_card)
        self.c_desc = CaptionLabel("High-frequency clicks with sub-ms spin timing.", self.clicker_card)
        self.c_desc.setWordWrap(True)
        self.btn_clicker = PushButton("⚡ Clicker", self.clicker_card)
        self.btn_clicker.clicked.connect(self.engine.toggle_clicker)
        c_layout.addWidget(self.c_title)
        c_layout.addWidget(self.c_desc)
        c_layout.addWidget(self.btn_clicker)

        self.triggers_grid.addWidget(self.record_card, 0, 0)
        self.triggers_grid.addWidget(self.play_card, 0, 1)
        self.triggers_grid.addWidget(self.clicker_card, 0, 2)

        actions_layout.addWidget(self.triggers_grid_container)
        self.layout.addWidget(self.actions_box)

    def build_telemetry_grid(self) -> None:
        self.stats_box = QWidget(self.container)
        stats_layout = QVBoxLayout(self.stats_box)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        stats_layout.setSpacing(8)

        self.telemetry_heading = StrongBodyLabel("Live Telemetry & Hotkeys", self.stats_box)
        stats_layout.addWidget(self.telemetry_heading)

        self.telemetry_grid_container = QWidget(self.stats_box)
        self.telemetry_grid = QGridLayout(self.telemetry_grid_container)
        self.telemetry_grid.setContentsMargins(0, 0, 0, 0)
        self.telemetry_grid.setSpacing(12)

        # Card 1: Macro Actions Loaded
        self.card1 = CardWidget(self.telemetry_grid_container)
        c1_l = QVBoxLayout(self.card1)
        c1_l.setContentsMargins(14, 12, 14, 12)
        self.c1_title = CaptionLabel("MACRO BUFFER", self.card1)
        self.metric_actions = TitleLabel("0 Actions", self.card1)
        self.metric_duration = CaptionLabel("Duration: 0.00s", self.card1)
        c1_l.addWidget(self.c1_title)
        c1_l.addWidget(self.metric_actions)
        c1_l.addWidget(self.metric_duration)

        # Card 2: Auto Clicker Counter
        self.card2 = CardWidget(self.telemetry_grid_container)
        c2_l = QVBoxLayout(self.card2)
        c2_l.setContentsMargins(14, 12, 14, 12)
        self.c2_title = CaptionLabel("CLICKS DISPATCHED", self.card2)
        self.metric_clicks = TitleLabel("0", self.card2)
        self.metric_click_rate = CaptionLabel("Interval: " + str(self.engine.settings.get("click_interval", "100")) + " ms", self.card2)
        c2_l.addWidget(self.c2_title)
        c2_l.addWidget(self.metric_clicks)
        c2_l.addWidget(self.metric_click_rate)

        # Card 3: Hotkey Cheat Sheet
        self.card3 = CardWidget(self.telemetry_grid_container)
        c3_l = QVBoxLayout(self.card3)
        c3_l.setContentsMargins(14, 12, 14, 12)
        self.c3_title = CaptionLabel("ACTIVE HOTKEYS", self.card3)
        
        self.hk_summary = BodyLabel(
            f"Record: {self.engine.settings.get('record_hotkey', 'F6')} | Play: {self.engine.settings.get('play_hotkey', 'F8')}\n"
            f"Clicker: {self.engine.settings.get('clicker_hotkey', 'F9')} | Panic: {self.engine.settings.get('panic_hotkey', 'F12')}",
            self.card3
        )
        self.hk_summary.setWordWrap(True)
        c3_l.addWidget(self.c3_title)
        c3_l.addWidget(self.hk_summary)

        self.telemetry_grid.addWidget(self.card1, 0, 0)
        self.telemetry_grid.addWidget(self.card2, 0, 1)
        self.telemetry_grid.addWidget(self.card3, 0, 2)

        stats_layout.addWidget(self.telemetry_grid_container)
        self.layout.addWidget(self.stats_box)

    def resizeEvent(self, event) -> None:
        """Responsive breakpoint handler for 3-column vs 1-column card layouts."""
        super().resizeEvent(event)
        width = self.width()

        if width < self.BREAKPOINT_WIDE and self._is_wide_layout:
            # Switch triggers to 1-column stack
            self.triggers_grid.removeWidget(self.record_card)
            self.triggers_grid.removeWidget(self.play_card)
            self.triggers_grid.removeWidget(self.clicker_card)
            self.triggers_grid.addWidget(self.record_card, 0, 0)
            self.triggers_grid.addWidget(self.play_card, 1, 0)
            self.triggers_grid.addWidget(self.clicker_card, 2, 0)

            # Switch telemetry to 1-column stack
            self.telemetry_grid.removeWidget(self.card1)
            self.telemetry_grid.removeWidget(self.card2)
            self.telemetry_grid.removeWidget(self.card3)
            self.telemetry_grid.addWidget(self.card1, 0, 0)
            self.telemetry_grid.addWidget(self.card2, 1, 0)
            self.telemetry_grid.addWidget(self.card3, 2, 0)
            self._is_wide_layout = False

        elif width >= self.BREAKPOINT_WIDE and not self._is_wide_layout:
            # Switch triggers back to 3-column row
            self.triggers_grid.removeWidget(self.record_card)
            self.triggers_grid.removeWidget(self.play_card)
            self.triggers_grid.removeWidget(self.clicker_card)
            self.triggers_grid.addWidget(self.record_card, 0, 0)
            self.triggers_grid.addWidget(self.play_card, 0, 1)
            self.triggers_grid.addWidget(self.clicker_card, 0, 2)

            # Switch telemetry back to 3-column row
            self.telemetry_grid.removeWidget(self.card1)
            self.telemetry_grid.removeWidget(self.card2)
            self.telemetry_grid.removeWidget(self.card3)
            self.telemetry_grid.addWidget(self.card1, 0, 0)
            self.telemetry_grid.addWidget(self.card2, 0, 1)
            self.telemetry_grid.addWidget(self.card3, 0, 2)
            self._is_wide_layout = True

    def update_theme(self) -> None:
        """Dynamically refresh all labels, hero banner, cards, and buttons on theme change."""
        is_dark = isDarkTheme()
        txt = get_text_colors(is_dark)
        c_style = card_style(is_dark)

        # Page Header
        self.page_title.setStyleSheet(f"font-size: 26px; font-weight: 700; color: {txt['primary']};")
        self.page_sub.setStyleSheet(f"font-size: 13px; color: {txt['muted']};")

        # Hero Card
        self.hero_card.setStyleSheet(hero_card_style(is_dark))
        self.system_status_label.setStyleSheet(f"font-weight: 600; font-size: 16px; color: {txt['primary']};")
        self.status_desc_label.setStyleSheet(f"color: {txt['secondary']}; font-size: 12px;")
        self.panic_hero_btn.setStyleSheet(panic_hero_button_style(is_dark))

        # Section Headings
        self.triggers_heading.setStyleSheet(f"font-size: 15px; color: {txt['primary']}; font-weight: 600;")
        self.telemetry_heading.setStyleSheet(f"font-size: 15px; color: {txt['primary']}; font-weight: 600;")

        # Quick Trigger Cards
        self.record_card.setStyleSheet(c_style)
        self.play_card.setStyleSheet(c_style)
        self.clicker_card.setStyleSheet(c_style)

        self.r_title.setStyleSheet(f"color: {txt['primary']}; font-size: 13px; font-weight: 600;")
        self.r_desc.setStyleSheet(f"color: {txt['muted']}; font-size: 11px;")
        self.p_title.setStyleSheet(f"color: {txt['primary']}; font-size: 13px; font-weight: 600;")
        self.p_desc.setStyleSheet(f"color: {txt['muted']}; font-size: 11px;")
        self.c_title.setStyleSheet(f"color: {txt['primary']}; font-size: 13px; font-weight: 600;")
        self.c_desc.setStyleSheet(f"color: {txt['muted']}; font-size: 11px;")

        # Telemetry Cards
        self.card1.setStyleSheet(c_style)
        self.card2.setStyleSheet(c_style)
        self.card3.setStyleSheet(c_style)

        self.c1_title.setStyleSheet(f"color: {txt['muted']}; font-weight: bold; font-size: 10px; letter-spacing: 0.5px;")
        self.c2_title.setStyleSheet(f"color: {txt['muted']}; font-weight: bold; font-size: 10px; letter-spacing: 0.5px;")
        self.c3_title.setStyleSheet(f"color: {txt['muted']}; font-weight: bold; font-size: 10px; letter-spacing: 0.5px;")

        metric_cyan = ThemeTokens.ACCENT_CYAN if is_dark else ThemeTokens.ACCENT_BLUE
        self.metric_actions.setStyleSheet(f"font-size: 20px; font-weight: 700; color: {metric_cyan};")
        self.metric_duration.setStyleSheet(f"color: {txt['dim']}; font-size: 11px;")

        metric_amber = ThemeTokens.ACCENT_AMBER if is_dark else "#d97706"
        self.metric_clicks.setStyleSheet(f"font-size: 20px; font-weight: 700; color: {metric_amber};")
        self.metric_click_rate.setStyleSheet(f"color: {txt['dim']}; font-size: 11px;")

        self.hk_summary.setStyleSheet(f"color: {txt['secondary']}; font-size: 11px; font-family: 'Consolas', 'Segoe UI', monospace;")

    def set_guarded(self, guarded: bool) -> None:
        """Disable primary execution buttons when viewing Settings tab to avoid accidental conflicts."""
        self._is_guarded = guarded
        if guarded:
            self.btn_record.setEnabled(False)
            self.btn_play.setEnabled(False)
            self.btn_clicker.setEnabled(False)
            self.btn_record.setToolTip("Execution controls disabled while configuring Settings")
            self.btn_play.setToolTip("Execution controls disabled while configuring Settings")
            self.btn_clicker.setToolTip("Execution controls disabled while configuring Settings")
        else:
            self.btn_record.setToolTip("")
            self.btn_play.setToolTip("")
            self.btn_clicker.setToolTip("")
            self.on_state_changed(self.engine.get_state())

    def on_state_changed(self, state: str) -> None:
        self.status_badge.set_state(state)

        if self._is_guarded:
            self.btn_record.setEnabled(False)
            self.btn_play.setEnabled(False)
            self.btn_clicker.setEnabled(False)
            return

        if state == "RECORDING":
            self.btn_record.setText("⏹ Stop")
            self.btn_record.setEnabled(True)
            self.btn_play.setEnabled(False)
            self.btn_clicker.setEnabled(False)
            self.status_desc_label.setText("Recording in progress... Actions are captured into buffer.")
        elif state == "PLAYING":
            self.btn_play.setText("⏹ Stop")
            self.btn_record.setEnabled(False)
            self.btn_play.setEnabled(True)
            self.btn_clicker.setEnabled(False)
            self.status_desc_label.setText("Playing recorded macro actions with precision scheduler.")
        elif state == "CLICKING":
            self.btn_clicker.setText("⏹ Stop")
            self.btn_record.setEnabled(False)
            self.btn_play.setEnabled(False)
            self.btn_clicker.setEnabled(True)
            self.status_desc_label.setText("Auto-clicker active. Firing rapid mouse clicks.")
        else:
            self.btn_record.setText("⏺ Record")
            self.btn_play.setText("▶ Play")
            self.btn_clicker.setText("⚡ Clicker")
            self.btn_record.setEnabled(True)
            self.btn_play.setEnabled(True)
            self.btn_clicker.setEnabled(True)
            self.status_desc_label.setText("Engine is idle and ready. Press a hotkey or trigger button.")

    def on_actions_updated(self, actions: list, duration: float) -> None:
        self.metric_actions.setText(f"{len(actions):,} Actions")
        self.metric_duration.setText(f"Duration: {duration:.2f}s")

    def on_clicker_progress(self, count: int) -> None:
        self.metric_clicks.setText(f"{count:,}")

    def on_clicker_finished(self, stopped: bool, count: int) -> None:
        self.metric_clicks.setText(f"{count:,}")

    def update_hotkey_summary(self) -> None:
        self.hk_summary.setText(
            f"Record: {self.engine.settings.get('record_hotkey', 'F6')} | Play: {self.engine.settings.get('play_hotkey', 'F8')}\n"
            f"Clicker: {self.engine.settings.get('clicker_hotkey', 'F9')} | Panic: {self.engine.settings.get('panic_hotkey', 'F12')}"
        )
        self.metric_click_rate.setText("Interval: " + str(self.engine.settings.get("click_interval", "100")) + " ms")
