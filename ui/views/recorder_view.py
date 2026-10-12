"""Macro Recorder & Player View - Windows 11 Fluent Recorder Suite with Virtualized Action Table & Responsive Breakpoints."""

from pathlib import Path
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QHeaderView, QFileDialog, QSizePolicy
)
from qfluentwidgets import (
    CardWidget, PrimaryPushButton, PushButton, LineEdit, ComboBox,
    SwitchButton, TableView, FluentIcon, TitleLabel, SubtitleLabel,
    BodyLabel, CaptionLabel, StrongBodyLabel, SmoothScrollArea,
    InfoBar, InfoBarPosition, isDarkTheme, qconfig
)

from ..components.status_badge import StatusBadge
from ..models.action_table_model import ActionTableModel
from ..theme import card_style, hero_card_style, table_style, get_text_colors, ThemeTokens


class RecorderView(SmoothScrollArea):
    """Modern Windows 11 Macro Recorder and Player with virtualized table inspector and responsive Bootstrap grid."""

    BREAKPOINT_WIDE = 820

    def __init__(self, engine, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.setObjectName("RecorderView")
        self._is_wide_layout = True
        self._is_guarded = False
        self._is_compact_view = False

        self.container = QWidget(self)
        self.setWidget(self.container)
        self.setWidgetResizable(True)
        self.setStyleSheet("background-color: transparent; border: none;")

        # Prevent horizontal geometry expansion and clipping
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

        self.page_title = TitleLabel("Macro Recorder & Player", title_box)
        self.page_sub = CaptionLabel("Capture keyboard and mouse streams with precision filtering & deterministic replay", title_box)
        self.page_sub.setWordWrap(True)

        title_layout.addWidget(self.page_title)
        title_layout.addWidget(self.page_sub)
        self.layout.addWidget(title_box)

        # Action Toolbar Banner Card
        self.build_toolbar_banner()

        # Playback & Motion Filter Grid (Responsive)
        self.build_controls_grid()

        # Virtualized Action Table Inspector
        self.build_actions_table_card()

        # JSON File Management Card
        self.build_file_card()

        self.layout.addStretch(1)

        # Connect engine signals
        self.engine.signals.state_changed.connect(self.on_state_changed)
        self.engine.signals.recording_progress.connect(self.on_recording_progress)
        self.engine.signals.actions_updated.connect(self.on_actions_updated)

        # Connect theme sync
        qconfig.themeChanged.connect(self.update_theme)

        # Explicitly apply theme on frame 0 to prevent unstyled white table on startup
        self.update_theme()

    def build_toolbar_banner(self) -> None:
        self.toolbar_card = CardWidget(self.container)
        t_layout = QHBoxLayout(self.toolbar_card)
        t_layout.setContentsMargins(18, 14, 18, 14)
        t_layout.setSpacing(14)

        # Left State & Actions Counter
        left_info = QWidget(self.toolbar_card)
        left_info.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        col_layout = QVBoxLayout(left_info)
        col_layout.setContentsMargins(0, 0, 0, 0)
        col_layout.setSpacing(3)

        row1 = QHBoxLayout()
        row1.setSpacing(10)
        self.t_title = SubtitleLabel("Macro Engine", left_info)
        self.badge = StatusBadge(left_info)
        row1.addWidget(self.t_title)
        row1.addWidget(self.badge)
        row1.addStretch(1)

        self.summary_label = CaptionLabel("0 action(s), 0.00 seconds recorded", left_info)
        self.summary_label.setWordWrap(True)
        col_layout.addLayout(row1)
        col_layout.addWidget(self.summary_label)
        t_layout.addWidget(left_info, 1)

        # Right Action Buttons
        btn_box = QWidget(self.toolbar_card)
        btn_layout = QHBoxLayout(btn_box)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(8)

        self.btn_record = PrimaryPushButton("⏺ Record", btn_box)
        self.btn_record.setFixedHeight(36)
        self.btn_record.clicked.connect(self.engine.toggle_recording)

        self.btn_play = PrimaryPushButton("▶ Play", btn_box)
        self.btn_play.setFixedHeight(36)
        self.btn_play.clicked.connect(self.engine.toggle_playback)

        self.btn_clear = PushButton("🗑 Clear", btn_box)
        self.btn_clear.setFixedHeight(36)
        self.btn_clear.clicked.connect(self.on_clear_clicked)

        btn_layout.addWidget(self.btn_record)
        btn_layout.addWidget(self.btn_play)
        btn_layout.addWidget(self.btn_clear)
        t_layout.addWidget(btn_box, 0)

        self.layout.addWidget(self.toolbar_card)

    def build_controls_grid(self) -> None:
        self.grid_container = QWidget(self.container)
        self.controls_layout = QGridLayout(self.grid_container)
        self.controls_layout.setContentsMargins(0, 0, 0, 0)
        self.controls_layout.setSpacing(14)

        # 1. Playback Configuration Card (2x2 grid for compact minimum width)
        self.play_card = CardWidget(self.grid_container)
        p_layout = QVBoxLayout(self.play_card)
        p_layout.setContentsMargins(16, 14, 16, 14)
        p_layout.setSpacing(10)

        self.p_title = StrongBodyLabel("Playback Settings", self.play_card)
        p_layout.addWidget(self.p_title)

        p_grid = QGridLayout()
        p_grid.setHorizontalSpacing(14)
        p_grid.setVerticalSpacing(8)

        # Repeat mode
        self.lbl_mode = BodyLabel("Repeat Mode", self.play_card)
        self.combo_mode = ComboBox(self.play_card)
        self.combo_mode.addItems(["Count", "Timer"])
        curr_mode = str(self.engine.settings.get("repeat_mode", "count")).title()
        self.combo_mode.setCurrentText(curr_mode if curr_mode in ["Count", "Timer"] else "Count")
        self.combo_mode.currentTextChanged.connect(self._save_playback_config)
        p_grid.addWidget(self.lbl_mode, 0, 0)
        p_grid.addWidget(self.combo_mode, 1, 0)

        # Repeat count
        self.lbl_count = BodyLabel("Loops", self.play_card)
        self.input_count = LineEdit(self.play_card)
        self.input_count.setText(str(self.engine.settings.get("repeat_count", "1")))
        self.input_count.textChanged.connect(self._save_playback_config)
        p_grid.addWidget(self.lbl_count, 0, 1)
        p_grid.addWidget(self.input_count, 1, 1)

        # Timer duration
        self.lbl_dur = BodyLabel("Duration (s)", self.play_card)
        self.input_duration = LineEdit(self.play_card)
        self.input_duration.setText(str(self.engine.settings.get("repeat_duration", "60")))
        self.input_duration.textChanged.connect(self._save_playback_config)
        p_grid.addWidget(self.lbl_dur, 2, 0)
        p_grid.addWidget(self.input_duration, 3, 0)

        # Speed
        self.lbl_speed = BodyLabel("Speed", self.play_card)
        self.combo_speed = ComboBox(self.play_card)
        self.combo_speed.addItems(["0.25", "0.5", "0.75", "1.0", "1.25", "1.5", "2.0", "3.0", "4.0"])
        curr_spd = str(self.engine.settings.get("playback_speed", "1.0"))
        self.combo_speed.setCurrentText(curr_spd)
        self.combo_speed.currentTextChanged.connect(self._save_playback_config)
        p_grid.addWidget(self.lbl_speed, 2, 1)
        p_grid.addWidget(self.combo_speed, 3, 1)

        p_layout.addLayout(p_grid)

        # 2. Movement Filter Card (compact 2-column layout)
        self.filter_card = CardWidget(self.grid_container)
        f_layout = QVBoxLayout(self.filter_card)
        f_layout.setContentsMargins(16, 14, 16, 14)
        f_layout.setSpacing(10)

        self.f_title = StrongBodyLabel("Movement Capture Filter", self.filter_card)
        f_layout.addWidget(self.f_title)

        f_grid = QGridLayout()
        f_grid.setHorizontalSpacing(14)
        f_grid.setVerticalSpacing(8)

        # Switch Record Moves
        self.lbl_moves = BodyLabel("Record Movements", self.filter_card)
        self.switch_moves = SwitchButton(self.filter_card)
        self.switch_moves.setChecked(bool(self.engine.settings.get("record_moves", True)))
        self.switch_moves.checkedChanged.connect(self._save_filter_config)
        f_grid.addWidget(self.lbl_moves, 0, 0, 1, 2)
        f_grid.addWidget(self.switch_moves, 1, 0, 1, 2)

        # Min Distance
        self.lbl_dist = BodyLabel("Min Distance (px)", self.filter_card)
        self.input_distance = LineEdit(self.filter_card)
        self.input_distance.setText(str(self.engine.settings.get("move_distance", "4")))
        self.input_distance.textChanged.connect(self._save_filter_config)
        f_grid.addWidget(self.lbl_dist, 2, 0)
        f_grid.addWidget(self.input_distance, 3, 0)

        # Min Interval
        self.lbl_int = BodyLabel("Min Interval (ms)", self.filter_card)
        self.input_interval = LineEdit(self.filter_card)
        self.input_interval.setText(str(self.engine.settings.get("move_interval", "20")))
        self.input_interval.textChanged.connect(self._save_filter_config)
        f_grid.addWidget(self.lbl_int, 2, 1)
        f_grid.addWidget(self.input_interval, 3, 1)

        f_layout.addLayout(f_grid)

        # Default 2-column placement
        self.controls_layout.addWidget(self.play_card, 0, 0)
        self.controls_layout.addWidget(self.filter_card, 0, 1)

        self.layout.addWidget(self.grid_container)

    def build_actions_table_card(self) -> None:
        self.table_card = CardWidget(self.container)
        self.table_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.table_card.setMinimumHeight(140)
        self.table_card.setFixedHeight(320)

        c_layout = QVBoxLayout(self.table_card)
        c_layout.setContentsMargins(16, 14, 16, 14)
        c_layout.setSpacing(8)

        header_row = QHBoxLayout()
        header_row.setSpacing(10)
        self.t_table_label = StrongBodyLabel("Action Buffer Inspector", self.table_card)
        self.table_count_label = CaptionLabel("Virtualized O(1) buffer view", self.table_card)
        
        self.btn_toggle_compact = PushButton("Compact (2-3 rows)", self.table_card, FluentIcon.MINIMIZE)
        self.btn_toggle_compact.setFixedHeight(28)
        self.btn_toggle_compact.clicked.connect(self.toggle_table_compact_view)

        header_row.addWidget(self.t_table_label)
        header_row.addWidget(self.table_count_label)
        header_row.addStretch(1)
        header_row.addWidget(self.btn_toggle_compact)
        c_layout.addLayout(header_row)

        # Virtualized TableView with flexible viewport
        self.table_model = ActionTableModel(self)
        self.action_table = TableView(self.table_card)
        self.action_table.setModel(self.table_model)
        self.action_table.setMinimumHeight(80)

        # Column width allocation: ample width for 5-digit row numbers, stretch for payload
        header = self.action_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)

        self.action_table.setColumnWidth(0, 65)
        self.action_table.setColumnWidth(1, 95)
        self.action_table.setColumnWidth(2, 125)

        self.action_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.action_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Apply initial theme stylesheet to action table
        self.action_table.setStyleSheet(table_style(isDarkTheme()))

        c_layout.addWidget(self.action_table)
        self.layout.addWidget(self.table_card)

    def toggle_table_compact_view(self) -> None:
        """Toggle table viewport between compact 2-3 rows (140px) and standard view (320px)."""
        self._is_compact_view = not self._is_compact_view
        if self._is_compact_view:
            self.table_card.setFixedHeight(140)
            self.btn_toggle_compact.setText("Expand View")
            self.btn_toggle_compact.setIcon(FluentIcon.FULL_SCREEN)
        else:
            self.table_card.setFixedHeight(320)
            self.btn_toggle_compact.setText("Compact (2-3 rows)")
            self.btn_toggle_compact.setIcon(FluentIcon.MINIMIZE)

    def build_file_card(self) -> None:
        self.file_card = CardWidget(self.container)
        c_layout = QHBoxLayout(self.file_card)
        c_layout.setContentsMargins(16, 12, 16, 12)
        c_layout.setSpacing(10)

        self.lbl_file = BodyLabel("Document:", self.file_card)
        self.input_filename = LineEdit(self.file_card)
        self.input_filename.setText(self.engine.current_filename)
        self.input_filename.setPlaceholderText("File name (without .json)")

        self.btn_save = PushButton("Save", self.file_card, FluentIcon.SAVE)
        self.btn_save.clicked.connect(self.on_save_clicked)

        self.btn_export = PushButton("Export", self.file_card, FluentIcon.SAVE_AS)
        self.btn_export.clicked.connect(self.on_export_clicked)

        self.btn_import = PushButton("Import", self.file_card, FluentIcon.FOLDER)
        self.btn_import.clicked.connect(self.on_import_clicked)

        c_layout.addWidget(self.lbl_file)
        c_layout.addWidget(self.input_filename, 1)
        c_layout.addWidget(self.btn_save)
        c_layout.addWidget(self.btn_export)
        c_layout.addWidget(self.btn_import)

        self.layout.addWidget(self.file_card)

    def update_theme(self) -> None:
        """Apply active theme palette across all cards, labels, and table views."""
        is_dark = isDarkTheme()
        txt = get_text_colors(is_dark)
        c_style = card_style(is_dark)

        # Page Header
        self.page_title.setStyleSheet(f"font-size: 26px; font-weight: 700; color: {txt['primary']};")
        self.page_sub.setStyleSheet(f"font-size: 13px; color: {txt['muted']};")

        # Toolbar Banner
        self.toolbar_card.setStyleSheet(hero_card_style(is_dark))
        self.t_title.setStyleSheet(f"font-weight: 600; font-size: 15px; color: {txt['primary']};")
        self.summary_label.setStyleSheet(f"color: {txt['secondary']}; font-size: 12px;")

        # Playback Card
        self.play_card.setStyleSheet(c_style)
        self.p_title.setStyleSheet(f"font-size: 14px; color: {txt['primary']}; font-weight: 600;")
        self.lbl_mode.setStyleSheet(f"color: {txt['secondary']}; font-size: 12px;")
        self.lbl_count.setStyleSheet(f"color: {txt['secondary']}; font-size: 12px;")
        self.lbl_dur.setStyleSheet(f"color: {txt['secondary']}; font-size: 12px;")
        self.lbl_speed.setStyleSheet(f"color: {txt['secondary']}; font-size: 12px;")

        # Movement Filter Card
        self.filter_card.setStyleSheet(c_style)
        self.f_title.setStyleSheet(f"font-size: 14px; color: {txt['primary']}; font-weight: 600;")
        self.lbl_moves.setStyleSheet(f"color: {txt['secondary']}; font-size: 12px;")
        self.lbl_dist.setStyleSheet(f"color: {txt['secondary']}; font-size: 12px;")
        self.lbl_int.setStyleSheet(f"color: {txt['secondary']}; font-size: 12px;")

        # Actions Table Card
        self.table_card.setStyleSheet(c_style)
        self.t_table_label.setStyleSheet(f"font-size: 14px; color: {txt['primary']}; font-weight: 600;")
        self.table_count_label.setStyleSheet(f"color: {txt['dim']}; font-size: 11px;")

        # Apply comprehensive table stylesheet from theme tokens
        self.action_table.setStyleSheet(table_style(is_dark))

        # File Card
        self.file_card.setStyleSheet(c_style)
        self.lbl_file.setStyleSheet(f"color: {txt['primary']}; font-weight: 600;")

    def resizeEvent(self, event) -> None:
        """Bootstrap-style breakpoint handler: stacks controls into 1-col on narrow views."""
        super().resizeEvent(event)
        width = self.width()

        if width < self.BREAKPOINT_WIDE and self._is_wide_layout:
            # Switch to 1-column stacked layout
            self.controls_layout.removeWidget(self.play_card)
            self.controls_layout.removeWidget(self.filter_card)
            self.controls_layout.addWidget(self.play_card, 0, 0)
            self.controls_layout.addWidget(self.filter_card, 1, 0)
            self._is_wide_layout = False

        elif width >= self.BREAKPOINT_WIDE and not self._is_wide_layout:
            # Switch to 2-column side-by-side grid
            self.controls_layout.removeWidget(self.play_card)
            self.controls_layout.removeWidget(self.filter_card)
            self.controls_layout.addWidget(self.play_card, 0, 0)
            self.controls_layout.addWidget(self.filter_card, 0, 1)
            self._is_wide_layout = True

    def _save_playback_config(self) -> None:
        self.engine.settings["repeat_mode"] = self.combo_mode.currentText().lower()
        self.engine.settings["repeat_count"] = self.input_count.text().strip() or "1"
        self.engine.settings["repeat_duration"] = self.input_duration.text().strip() or "60"
        self.engine.settings["playback_speed"] = self.combo_speed.currentText()
        self.engine.save_settings()

    def _save_filter_config(self) -> None:
        self.engine.settings["record_moves"] = self.switch_moves.isChecked()
        self.engine.settings["move_distance"] = self.input_distance.text().strip() or "4"
        self.engine.settings["move_interval"] = self.input_interval.text().strip() or "20"
        self.engine.save_settings()

    def on_clear_clicked(self) -> None:
        self.engine.clear_recording()
        self.table_model.clear()

    def on_save_clicked(self) -> None:
        name = self.input_filename.text().strip()
        try:
            dest = self.engine.save_recording(name)
            InfoBar.success(
                title="Recording Saved",
                content=f"Saved to {dest.name}",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self.window()
            )
        except Exception as exc:
            InfoBar.error(
                title="Save Error",
                content=str(exc),
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=4000,
                parent=self.window()
            )

    def on_export_clicked(self) -> None:
        name = self.input_filename.text().strip() or "macro"
        initial_file = str(Path(self.engine.save_recording(name)))
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Macro Recording",
            initial_file,
            "JSON files (*.json)"
        )
        if path:
            try:
                self.engine.export_recording(path)
                InfoBar.success(
                    title="Export Complete",
                    content=f"Exported to {Path(path).name}",
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self.window()
                )
            except Exception as exc:
                InfoBar.error(
                    title="Export Error",
                    content=str(exc),
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=4000,
                    parent=self.window()
                )

    def on_import_clicked(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Macro Recording",
            str(self.engine.load_settings()),
            "JSON files (*.json);;All Files (*.*)"
        )
        if path:
            try:
                count = self.engine.import_recording(path)
                self.input_filename.setText(Path(path).stem)
                InfoBar.success(
                    title="Import Successful",
                    content=f"Loaded {count:,} actions from {Path(path).name}",
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self.window()
                )
            except Exception as exc:
                InfoBar.error(
                    title="Import Failed",
                    content=f"Validation failed: {exc}",
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=4000,
                    parent=self.window()
                )

    def set_guarded(self, guarded: bool) -> None:
        """Disable primary execution buttons when viewing Settings tab to avoid accidental conflicts."""
        self._is_guarded = guarded
        if guarded:
            self.btn_record.setEnabled(False)
            self.btn_play.setEnabled(False)
            self.btn_clear.setEnabled(False)
            self.btn_record.setToolTip("Execution controls disabled while configuring Settings")
            self.btn_play.setToolTip("Execution controls disabled while configuring Settings")
            self.btn_clear.setToolTip("Execution controls disabled while configuring Settings")
        else:
            self.btn_record.setToolTip("")
            self.btn_play.setToolTip("")
            self.btn_clear.setToolTip("")
            self.on_state_changed(self.engine.get_state())

    def on_state_changed(self, state: str) -> None:
        self.badge.set_state(state)
        if self._is_guarded:
            self.btn_record.setEnabled(False)
            self.btn_play.setEnabled(False)
            self.btn_clear.setEnabled(False)
            return

        if state == "RECORDING":
            self.btn_record.setText("⏹ Stop")
            self.btn_record.setEnabled(True)
            self.btn_play.setEnabled(False)
            self.btn_clear.setEnabled(False)
        elif state == "PLAYING":
            self.btn_play.setText("⏹ Stop")
            self.btn_record.setEnabled(False)
            self.btn_play.setEnabled(True)
            self.btn_clear.setEnabled(False)
        elif state == "CLICKING":
            self.btn_record.setEnabled(False)
            self.btn_play.setEnabled(False)
            self.btn_clear.setEnabled(False)
        else:
            self.btn_record.setText("⏺ Record")
            self.btn_play.setText("▶ Play")
            self.btn_record.setEnabled(True)
            self.btn_play.setEnabled(True)
            self.btn_clear.setEnabled(True)

    def on_recording_progress(self, count: int, duration: float) -> None:
        """Throttled 30 FPS progress update during active recording (zero table redraw lag)."""
        self.summary_label.setText(f"{count:,} action(s), {duration:.2f} seconds recorded")
        self.table_count_label.setText(f"{count:,} actions captured")

    def on_actions_updated(self, actions: list, duration: float) -> None:
        """Atomic table model update on recording completion, clear, or import."""
        self.table_model.set_actions(actions)
        self.summary_label.setText(f"{len(actions):,} action(s), {duration:.2f} seconds recorded")
        self.table_count_label.setText(f"{len(actions):,} actions in buffer")
        if actions:
            self.action_table.scrollToBottom()
