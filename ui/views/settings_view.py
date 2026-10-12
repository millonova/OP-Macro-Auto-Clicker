"""Settings View - Windows 11 Fluent Settings Panel with 3-Way Theme Sync & Windows Accent Matching."""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QMessageBox, QSizePolicy
)
from qfluentwidgets import (
    CardWidget, PushButton, PrimaryPushButton, SwitchButton, ComboBox,
    FluentIcon, TitleLabel, SubtitleLabel, BodyLabel, CaptionLabel,
    StrongBodyLabel, SmoothScrollArea, InfoBar, InfoBarPosition,
    isDarkTheme, qconfig
)

from ..components.hotkey_card import HotkeyRowCard
from ..theme import (
    card_style, danger_card_style, danger_button_style, get_text_colors,
    apply_theme_mode, ThemeTokens
)


class SettingsView(SmoothScrollArea):
    """Windows 11 Settings-style configuration panel for hotkeys, system theme modes, and app behaviors."""

    hotkey_changed = pyqtSignal()
    theme_mode_changed = pyqtSignal(str)

    def __init__(self, engine, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.setObjectName("SettingsView")

        self.container = QWidget(self)
        self.setWidget(self.container)
        self.setWidgetResizable(True)
        self.setStyleSheet("background-color: transparent; border: none;")

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.layout = QVBoxLayout(self.container)
        self.layout.setContentsMargins(24, 20, 24, 24)
        self.layout.setSpacing(20)

        # Header Title Box
        title_box = QWidget(self.container)
        title_layout = QVBoxLayout(title_box)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(4)

        self.page_title = TitleLabel("Settings & Configuration", title_box)
        self.page_sub = CaptionLabel("Manage global keybindings, native Windows 11 theme sync, visual appearance, and emergency controls", title_box)
        self.page_sub.setWordWrap(True)

        title_layout.addWidget(self.page_title)
        title_layout.addWidget(self.page_sub)
        self.layout.addWidget(title_box)

        # 1. Global Hotkeys Section
        self.build_hotkeys_section()

        # 2. Window Behavior & Theme Section
        self.build_appearance_section()

        # 3. Danger Zone Section
        self.build_danger_zone()

        self.layout.addStretch(1)

        # Connect engine signals
        self.engine.signals.hotkey_captured.connect(self.on_hotkey_captured)
        self.engine.signals.hotkey_conflict.connect(self.on_hotkey_conflict)
        self.engine.signals.hotkey_capture_cancelled.connect(self.on_hotkey_capture_cancelled)

        # Connect theme sync
        qconfig.themeChanged.connect(self.update_theme)
        self.update_theme()

    def build_hotkeys_section(self) -> None:
        self.hotkeys_section = QWidget(self.container)
        s_layout = QVBoxLayout(self.hotkeys_section)
        s_layout.setContentsMargins(0, 0, 0, 0)
        s_layout.setSpacing(10)

        self.hotkeys_title = StrongBodyLabel("Global Keybindings", self.hotkeys_section)
        self.hotkeys_desc = CaptionLabel("Key combinations are intercepted system-wide across all active applications.", self.hotkeys_section)
        self.hotkeys_desc.setWordWrap(True)
        s_layout.addWidget(self.hotkeys_title)
        s_layout.addWidget(self.hotkeys_desc)

        # Hotkey rows
        self.rows: dict[str, HotkeyRowCard] = {}

        hotkey_defs = [
            ("record", "Toggle Recording", "Start or stop capturing inputs into the active buffer", str(self.engine.settings.get("record_hotkey", "Ctrl+1"))),
            ("play", "Toggle Playback", "Start or halt macro execution cycle", str(self.engine.settings.get("play_hotkey", "Ctrl+2"))),
            ("clicker", "Toggle Auto Clicker", "Trigger or stop high-speed automated mouse clicks", str(self.engine.settings.get("clicker_hotkey", "Ctrl+3"))),
            ("stop_all", "Panic Stop (Halt All)", "Emergency kill-switch to immediately abort all macro and clicker actions", str(self.engine.settings.get("panic_hotkey", "F12"))),
            ("force_exit", "Emergency Force Exit", "Directly terminate the application process without prompts", str(self.engine.settings.get("force_exit_hotkey", "F11"))),
        ]

        for action_name, title_txt, desc_txt, current_key in hotkey_defs:
            card = HotkeyRowCard(action_name, title_txt, desc_txt, current_key, self.hotkeys_section)
            card.capture_requested.connect(self.on_capture_requested)
            self.rows[action_name] = card
            s_layout.addWidget(card)

        self.layout.addWidget(self.hotkeys_section)

    def build_appearance_section(self) -> None:
        self.app_section = QWidget(self.container)
        s_layout = QVBoxLayout(self.app_section)
        s_layout.setContentsMargins(0, 0, 0, 0)
        s_layout.setSpacing(10)

        self.app_title = StrongBodyLabel("Window & Appearance", self.app_section)
        s_layout.addWidget(self.app_title)

        # 1. 3-Way Theme Mode Card
        self.card_theme = CardWidget(self.app_section)
        c_th_l = QHBoxLayout(self.card_theme)
        c_th_l.setContentsMargins(16, 14, 16, 14)
        c_th_l.setSpacing(16)

        th_txt_box = QWidget(self.card_theme)
        th_txt_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        th_txt_l = QVBoxLayout(th_txt_box)
        th_txt_l.setContentsMargins(0, 0, 0, 0)
        th_txt_l.setSpacing(2)
        self.lbl_th = BodyLabel("App Theme & Color Mode", self.card_theme)
        self.desc_th = CaptionLabel("Sync automatically with Windows 11 system theme or enforce Dark / Light styling", self.card_theme)
        self.desc_th.setWordWrap(True)
        th_txt_l.addWidget(self.lbl_th)
        th_txt_l.addWidget(self.desc_th)

        self.combo_theme = ComboBox(self.card_theme)
        self.combo_theme.addItems(["System Default", "Dark Mode", "Light Mode"])
        self.combo_theme.setMinimumWidth(150)

        saved_mode = str(self.engine.settings.get("theme_mode", "system")).lower()
        if saved_mode == "dark":
            self.combo_theme.setCurrentText("Dark Mode")
        elif saved_mode == "light":
            self.combo_theme.setCurrentText("Light Mode")
        else:
            self.combo_theme.setCurrentText("System Default")

        self.combo_theme.currentTextChanged.connect(self.on_theme_mode_changed)

        c_th_l.addWidget(th_txt_box, 1)
        c_th_l.addWidget(self.combo_theme, 0)
        s_layout.addWidget(self.card_theme)

        # 2. Always on top card
        self.card_top = CardWidget(self.app_section)
        c_top_l = QHBoxLayout(self.card_top)
        c_top_l.setContentsMargins(16, 14, 16, 14)
        c_top_l.setSpacing(16)

        txt_box = QWidget(self.card_top)
        txt_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        txt_l = QVBoxLayout(txt_box)
        txt_l.setContentsMargins(0, 0, 0, 0)
        txt_l.setSpacing(2)
        self.lbl_top = BodyLabel("Always On Top", txt_box)
        self.desc_top = CaptionLabel("Keep Macro Plus floating above all other desktop windows", txt_box)
        self.desc_top.setWordWrap(True)
        txt_l.addWidget(self.lbl_top)
        txt_l.addWidget(self.desc_top)

        self.switch_top = SwitchButton(self.card_top)
        self.switch_top.setChecked(bool(self.engine.settings.get("always_on_top", False)))
        self.switch_top.checkedChanged.connect(self.on_always_on_top_toggled)

        c_top_l.addWidget(txt_box, 1)
        c_top_l.addWidget(self.switch_top, 0)
        s_layout.addWidget(self.card_top)

        self.layout.addWidget(self.app_section)

    def build_danger_zone(self) -> None:
        self.danger_section = QWidget(self.container)
        s_layout = QVBoxLayout(self.danger_section)
        s_layout.setContentsMargins(0, 0, 0, 0)
        s_layout.setSpacing(10)

        self.danger_heading = StrongBodyLabel("Emergency & Termination", self.danger_section)
        s_layout.addWidget(self.danger_heading)

        self.card_danger = CardWidget(self.danger_section)
        d_layout = QHBoxLayout(self.card_danger)
        d_layout.setContentsMargins(16, 14, 16, 14)
        d_layout.setSpacing(16)

        txt_box = QWidget(self.card_danger)
        txt_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        txt_l = QVBoxLayout(txt_box)
        txt_l.setContentsMargins(0, 0, 0, 0)
        txt_l.setSpacing(2)
        self.lbl_d = BodyLabel("Emergency Force Exit", txt_box)
        self.desc_d = CaptionLabel("Force terminates all worker threads and closes the app instantly without prompting.", txt_box)
        self.desc_d.setWordWrap(True)
        txt_l.addWidget(self.lbl_d)
        txt_l.addWidget(self.desc_d)

        self.btn_exit = PushButton("Force Exit Now", self.card_danger)
        self.btn_exit.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.btn_exit.setMinimumSize(130, 36)
        self.btn_exit.clicked.connect(self.on_force_exit_clicked)

        d_layout.addWidget(txt_box, 1)
        d_layout.addWidget(self.btn_exit, 0)
        s_layout.addWidget(self.card_danger)

        self.layout.addWidget(self.danger_section)

    def update_theme(self) -> None:
        is_dark = isDarkTheme()
        txt = get_text_colors(is_dark)
        c_style = card_style(is_dark)

        # Page Header
        self.page_title.setStyleSheet(f"font-size: 26px; font-weight: 700; color: {txt['primary']};")
        self.page_sub.setStyleSheet(f"font-size: 13px; color: {txt['muted']};")

        # Section Headings
        self.hotkeys_title.setStyleSheet(f"font-size: 16px; color: {txt['primary']}; font-weight: 600;")
        self.hotkeys_desc.setStyleSheet(f"color: {txt['muted']}; font-size: 12px;")
        self.app_title.setStyleSheet(f"font-size: 16px; color: {txt['primary']}; font-weight: 600;")

        # Appearance Cards
        self.card_top.setStyleSheet(c_style)
        self.card_theme.setStyleSheet(c_style)

        self.lbl_top.setStyleSheet(f"font-weight: 600; font-size: 13px; color: {txt['primary']};")
        self.desc_top.setStyleSheet(f"color: {txt['muted']}; font-size: 11px;")
        self.lbl_th.setStyleSheet(f"font-weight: 600; font-size: 13px; color: {txt['primary']};")
        self.desc_th.setStyleSheet(f"color: {txt['muted']}; font-size: 11px;")

        # Danger Card
        self.danger_heading.setStyleSheet("font-size: 16px; color: #ef4444; font-weight: 600;")
        self.card_danger.setStyleSheet(danger_card_style(is_dark))
        danger_text_color = "#fca5a5" if is_dark else "#dc2626"
        danger_desc_color = "#f87171" if is_dark else "#ef4444"
        self.lbl_d.setStyleSheet(f"font-weight: 600; font-size: 13px; color: {danger_text_color};")
        self.desc_d.setStyleSheet(f"color: {danger_desc_color}; font-size: 11px;")
        self.btn_exit.setStyleSheet(danger_button_style(is_dark))

    def on_capture_requested(self, action_name: str) -> None:
        for name, row in self.rows.items():
            row.set_capturing(name == action_name)
        self.engine.arm_hotkey_capture(action_name)

    def on_hotkey_captured(self, action_name: str, hotkey: str) -> None:
        if action_name in self.rows:
            self.rows[action_name].update_key_badge(hotkey)
            self.rows[action_name].set_capturing(False)
        self.hotkey_changed.emit()

    def on_hotkey_conflict(self, action_name: str, hotkey: str) -> None:
        if action_name in self.rows:
            self.rows[action_name].show_conflict(hotkey)

    def on_hotkey_capture_cancelled(self) -> None:
        for name, row in self.rows.items():
            row.set_capturing(False)
            setting_key = {
                "record": "record_hotkey",
                "play": "play_hotkey",
                "clicker": "clicker_hotkey",
                "stop_all": "panic_hotkey",
                "force_exit": "force_exit_hotkey"
            }.get(name)
            if setting_key:
                row.update_key_badge(str(self.engine.settings.get(setting_key, "")))

    def on_always_on_top_toggled(self, checked: bool) -> None:
        self.engine.settings["always_on_top"] = checked
        self.engine.save_settings()
        win = self.window()
        if win:
            if checked:
                win.setWindowFlags(win.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
            else:
                win.setWindowFlags(win.windowFlags() & ~Qt.WindowType.WindowStaysOnTopHint)
            win.show()

    def on_theme_mode_changed(self, mode_text: str) -> None:
        mode_key = {
            "System Default": "system",
            "Dark Mode": "dark",
            "Light Mode": "light"
        }.get(mode_text, "system")

        self.engine.settings["theme_mode"] = mode_key
        self.engine.save_settings()
        apply_theme_mode(mode_key)
        self.theme_mode_changed.emit(mode_key)

    def on_force_exit_clicked(self) -> None:
        reply = QMessageBox.question(
            self,
            "Emergency Force Exit",
            "Are you sure you want to terminate Macro Plus immediately?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.engine.force_exit()
