"""Main Fluent Application Window for Macro Plus with Windows 11 Accent & System Theme Sync."""

import sys
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QApplication
from qfluentwidgets import (
    FluentWindow, NavigationItemPosition, FluentIcon,
    InfoBar, InfoBarPosition, isDarkTheme, qconfig
)

from .theme import (
    ThemeTokens, apply_theme_mode, sync_system_accent,
    get_windows_system_is_dark, get_windows_accent_color
)
from .views.dashboard_view import DashboardView
from .views.clicker_view import ClickerView
from .views.recorder_view import RecorderView
from .views.settings_view import SettingsView


class MacroPlusWindow(FluentWindow):
    """Modern Windows 11 Settings-style Main Application Window with OS theme and accent synchronization."""

    def __init__(self, engine, parent=None):
        super().__init__(parent)
        self.engine = engine

        self.setWindowTitle("OP Macro & Auto Clicker - Windows 11 Precision Suite")
        self.resize(1080, 740)
        self.setMinimumSize(840, 560)

        # Solid background for consistent appearance
        self.setMicaEffectEnabled(False)
        self.setCustomBackgroundColor(
            QColor(ThemeTokens.LIGHT_WINDOW_BG),
            QColor(ThemeTokens.DARK_WINDOW_BG)
        )

        # Sidebar navigation sizing
        self.navigationInterface.setExpandWidth(220)
        self.navigationInterface.setMinimumExpandWidth(190)

        # Initial Theme & Accent setup from settings
        initial_mode = str(self.engine.settings.get("theme_mode", "system"))
        apply_theme_mode(initial_mode)

        # Initialize Views
        self.dashboard_view = DashboardView(self.engine, self)
        self.clicker_view = ClickerView(self.engine, self)
        self.recorder_view = RecorderView(self.engine, self)
        self.settings_view = SettingsView(self.engine, self)

        # Hook navigation sub-interfaces
        self.init_navigation()

        # Hook navigation page switch to guard controls on settings view
        self.stackedWidget.currentChanged.connect(self._on_navigation_changed)

        # Connect notifications and settings signals
        self.engine.signals.notification_requested.connect(self.show_toast)
        self.settings_view.hotkey_changed.connect(self.dashboard_view.update_hotkey_summary)

        # Apply Always on Top if configured
        if self.engine.settings.get("always_on_top", False):
            self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)

        # Center on screen
        self._center_window()

        # Setup OS theme & accent sync polling timer (1.5s interval, non-blocking)
        self._last_system_dark = get_windows_system_is_dark()
        self._last_accent = get_windows_accent_color()
        self._sync_timer = QTimer(self)
        self._sync_timer.setInterval(1500)
        self._sync_timer.timeout.connect(self._check_os_theme_sync)
        self._sync_timer.start()

    def init_navigation(self) -> None:
        """Populate left sidebar navigation tabs."""
        self.addSubInterface(
            self.dashboard_view,
            FluentIcon.HOME,
            "Dashboard",
            position=NavigationItemPosition.TOP
        )
        self.addSubInterface(
            self.clicker_view,
            FluentIcon.SPEED_HIGH,
            "Auto Clicker",
            position=NavigationItemPosition.TOP
        )
        self.addSubInterface(
            self.recorder_view,
            FluentIcon.VIDEO,
            "Macro Recorder",
            position=NavigationItemPosition.TOP
        )
        self.addSubInterface(
            self.settings_view,
            FluentIcon.SETTING,
            "Settings",
            position=NavigationItemPosition.BOTTOM
        )

    def _on_navigation_changed(self, index: int) -> None:
        """Guard primary execution buttons and global hotkeys when viewing Settings tab, restore on return."""
        current_view = self.stackedWidget.widget(index)
        is_settings = (current_view == self.settings_view)
        self.engine.set_guarded(is_settings)
        self.dashboard_view.set_guarded(is_settings)
        self.recorder_view.set_guarded(is_settings)
        self.clicker_view.set_guarded(is_settings)

    def _check_os_theme_sync(self) -> None:
        """Check for Windows 11 system theme or accent color changes in background."""
        current_mode = str(self.engine.settings.get("theme_mode", "system")).lower()

        # 1. Sync Accent Color if changed
        current_accent = get_windows_accent_color()
        if current_accent != self._last_accent:
            self._last_accent = current_accent
            sync_system_accent()
            self._broadcast_theme_update()

        # 2. Sync Dark/Light if in System Default mode
        if current_mode == "system":
            current_system_dark = get_windows_system_is_dark()
            if current_system_dark != self._last_system_dark or current_system_dark != isDarkTheme():
                self._last_system_dark = current_system_dark
                apply_theme_mode("system")
                self._broadcast_theme_update()

    def _broadcast_theme_update(self) -> None:
        """Trigger theme update across all child views."""
        self.dashboard_view.update_theme()
        self.clicker_view.update_theme()
        self.recorder_view.update_theme()
        self.settings_view.update_theme()

    def _center_window(self) -> None:
        screen = QApplication.primaryScreen()
        if screen:
            screen_geo = screen.availableGeometry()
            x = (screen_geo.width() - self.width()) // 2
            y = (screen_geo.height() - self.height()) // 2
            self.move(x, y)

    def show_toast(self, severity: str, title: str, message: str) -> None:
        bar_func = {
            "success": InfoBar.success,
            "warning": InfoBar.warning,
            "error": InfoBar.error,
            "info": InfoBar.info
        }.get(severity, InfoBar.info)

        bar_func(
            title=title,
            content=message,
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=3500,
            parent=self
        )

    def closeEvent(self, event) -> None:
        """Gracefully release high-res timer, sync loop, and stop global listeners on exit."""
        if hasattr(self, "_sync_timer"):
            self._sync_timer.stop()
        self.engine.shutdown()
        event.accept()
