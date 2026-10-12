"""Centralized UI Theme Tokens and Dynamic Stylesheet Generators for Macro Plus.

Supports seamless live switching between Windows 11 Dark Mode, Light Mode, and System Default,
automatically synchronized with native Windows 11 accent colors and dark mode registry settings.
"""

from __future__ import annotations
import sys
from PyQt6.QtGui import QColor
from qfluentwidgets import isDarkTheme, setTheme, setThemeColor, Theme


def get_windows_system_is_dark() -> bool:
    """Return True if Windows system is in Dark mode, False for Light mode."""
    if sys.platform == "win32":
        try:
            import winreg
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
            ) as key:
                val, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                return val == 0
        except Exception:
            pass
    return True


def get_windows_accent_color() -> str:
    """Return the Windows 11 system accent color hex string (e.g. #0078d4), falling back to Fluent Blue."""
    if sys.platform == "win32":
        try:
            import winreg
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\DWM"
            ) as key:
                val, _ = winreg.QueryValueEx(key, "AccentColor")
                # AccentColor is DWORD 0xAABBGGRR
                r = val & 0xFF
                g = (val >> 8) & 0xFF
                b = (val >> 16) & 0xFF
                return f"#{r:02x}{g:02x}{b:02x}"
        except Exception:
            try:
                import winreg
                with winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\DWM"
                ) as key:
                    val, _ = winreg.QueryValueEx(key, "ColorizationColor")
                    # ColorizationColor is DWORD 0xAARRGGBB
                    r = (val >> 16) & 0xFF
                    g = (val >> 8) & 0xFF
                    b = val & 0xFF
                    return f"#{r:02x}{g:02x}{b:02x}"
            except Exception:
                pass
    return "#0078d4"


class ThemeTokens:
    """Design tokens matching Windows 11 Fluent and Antigravity IDE palettes."""

    # Active system accent color
    ACTIVE_ACCENT = get_windows_accent_color()

    # --- ACCENT & STATUS HUES ---
    ACCENT_CYAN = "#0ea5e9"
    ACCENT_BLUE = "#0284c7"
    ACCENT_EMERALD = "#10b981"
    ACCENT_AMBER = "#f59e0b"
    ACCENT_ROSE = "#f43f5e"

    # --- DARK THEME PALETTE ---
    DARK_WINDOW_BG = "#181818"
    DARK_PANEL_BG = "#1e1e1e"
    DARK_CARD_BG = "rgba(255, 255, 255, 0.035)"
    DARK_CARD_HOVER = "rgba(255, 255, 255, 0.065)"
    DARK_CARD_BORDER = "rgba(255, 255, 255, 0.08)"
    DARK_CARD_BORDER_HOVER = "rgba(255, 255, 255, 0.14)"

    DARK_HERO_BG = "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1e293b, stop:1 #0f172a)"
    DARK_HERO_BORDER = "rgba(255, 255, 255, 0.12)"

    DARK_TEXT_PRIMARY = "#f8fafc"
    DARK_TEXT_SECONDARY = "#cbd5e1"
    DARK_TEXT_MUTED = "#94a3b8"
    DARK_TEXT_DIM = "#64748b"

    DARK_TABLE_BG = "#1b1b1b"
    DARK_TABLE_HEADER_BG = "#242424"
    DARK_TABLE_BORDER = "rgba(255, 255, 255, 0.08)"
    DARK_TABLE_GRID = "rgba(255, 255, 255, 0.05)"
    DARK_TABLE_TEXT = "#e2e8f0"

    # --- LIGHT THEME PALETTE ---
    LIGHT_WINDOW_BG = "#f3f3f3"
    LIGHT_PANEL_BG = "#f9f9f9"
    LIGHT_CARD_BG = "#ffffff"
    LIGHT_CARD_HOVER = "#f8fafc"
    LIGHT_CARD_BORDER = "rgba(0, 0, 0, 0.08)"
    LIGHT_CARD_BORDER_HOVER = "rgba(0, 0, 0, 0.14)"

    LIGHT_HERO_BG = "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #f8fafc, stop:1 #f1f5f9)"
    LIGHT_HERO_BORDER = "rgba(0, 0, 0, 0.09)"

    LIGHT_TEXT_PRIMARY = "#0f172a"
    LIGHT_TEXT_SECONDARY = "#334155"
    LIGHT_TEXT_MUTED = "#64748b"
    LIGHT_TEXT_DIM = "#94a3b8"

    LIGHT_TABLE_BG = "#ffffff"
    LIGHT_TABLE_HEADER_BG = "#f1f5f9"
    LIGHT_TABLE_BORDER = "rgba(0, 0, 0, 0.08)"
    LIGHT_TABLE_GRID = "rgba(0, 0, 0, 0.04)"
    LIGHT_TABLE_TEXT = "#1e293b"


def sync_system_accent() -> str:
    """Re-query Windows 11 system accent color and update theme engine."""
    accent = get_windows_accent_color()
    ThemeTokens.ACTIVE_ACCENT = accent
    setThemeColor(QColor(accent))
    return accent


def apply_theme_mode(mode: str) -> bool:
    """
    Apply theme mode: 'system', 'dark', or 'light'.
    Returns True if target theme is Dark, False if Light.
    """
    sync_system_accent()
    m = mode.lower().strip()
    if m == "system":
        is_dark = get_windows_system_is_dark()
    elif m == "light":
        is_dark = False
    else:
        is_dark = True

    setTheme(Theme.DARK if is_dark else Theme.LIGHT)
    return is_dark


def card_style(dark: bool | None = None) -> str:
    """Return standard CardWidget stylesheet for current theme."""
    is_dark = isDarkTheme() if dark is None else dark
    if is_dark:
        return f"""
            CardWidget {{
                background-color: {ThemeTokens.DARK_CARD_BG};
                border: 1px solid {ThemeTokens.DARK_CARD_BORDER};
                border-radius: 10px;
            }}
            CardWidget:hover {{
                background-color: {ThemeTokens.DARK_CARD_HOVER};
                border: 1px solid {ThemeTokens.DARK_CARD_BORDER_HOVER};
            }}
        """
    return f"""
        CardWidget {{
            background-color: {ThemeTokens.LIGHT_CARD_BG};
            border: 1px solid {ThemeTokens.LIGHT_CARD_BORDER};
            border-radius: 10px;
        }}
        CardWidget:hover {{
            background-color: {ThemeTokens.LIGHT_CARD_HOVER};
            border: 1px solid {ThemeTokens.LIGHT_CARD_BORDER_HOVER};
        }}
    """


def hero_card_style(dark: bool | None = None) -> str:
    """Return top Hero / Banner Card stylesheet for current theme."""
    is_dark = isDarkTheme() if dark is None else dark
    if is_dark:
        return f"""
            CardWidget {{
                background: {ThemeTokens.DARK_HERO_BG};
                border: 1px solid {ThemeTokens.DARK_HERO_BORDER};
                border-radius: 12px;
            }}
        """
    return f"""
        CardWidget {{
            background: {ThemeTokens.LIGHT_HERO_BG};
            border: 1px solid {ThemeTokens.LIGHT_HERO_BORDER};
            border-radius: 12px;
        }}
    """


def danger_card_style(dark: bool | None = None) -> str:
    """Return Emergency Danger Card stylesheet for current theme."""
    is_dark = isDarkTheme() if dark is None else dark
    if is_dark:
        return """
            CardWidget {
                border-radius: 8px;
                border: 1px solid rgba(239, 68, 68, 0.35);
                background-color: rgba(239, 68, 68, 0.06);
            }
            CardWidget:hover {
                border: 1px solid rgba(239, 68, 68, 0.5);
                background-color: rgba(239, 68, 68, 0.09);
            }
        """
    return """
        CardWidget {
            border-radius: 8px;
            border: 1px solid rgba(220, 38, 38, 0.3);
            background-color: rgba(254, 242, 242, 0.8);
        }
        CardWidget:hover {
            border: 1px solid rgba(220, 38, 38, 0.45);
            background-color: rgba(254, 226, 226, 0.9);
        }
    """


def danger_button_style(dark: bool | None = None) -> str:
    """Return Emergency Force Exit button stylesheet."""
    is_dark = isDarkTheme() if dark is None else dark
    if is_dark:
        return """
            PushButton {
                background-color: rgba(239, 68, 68, 0.22);
                color: #fca5a5;
                border: 1px solid rgba(239, 68, 68, 0.45);
                font-weight: 700;
                font-size: 13px;
                border-radius: 6px;
                padding: 6px 14px;
            }
            PushButton:hover {
                background-color: #dc2626;
                color: #ffffff;
                border: 1px solid #ef4444;
            }
            PushButton:pressed {
                background-color: #b91c1c;
                color: #ffffff;
            }
        """
    return """
        PushButton {
            background-color: rgba(239, 68, 68, 0.12);
            color: #dc2626;
            border: 1px solid rgba(239, 68, 68, 0.35);
            font-weight: 700;
            font-size: 13px;
            border-radius: 6px;
            padding: 6px 14px;
        }
        PushButton:hover {
            background-color: #dc2626;
            color: #ffffff;
            border: 1px solid #dc2626;
        }
        PushButton:pressed {
            background-color: #b91c1c;
            color: #ffffff;
        }
    """


def panic_hero_button_style(dark: bool | None = None) -> str:
    """Return Panic Stop hero button stylesheet."""
    is_dark = isDarkTheme() if dark is None else dark
    if is_dark:
        return """
            PushButton {
                background-color: rgba(239, 68, 68, 0.18);
                color: #f87171;
                border: 1px solid rgba(239, 68, 68, 0.4);
                font-weight: 700;
                font-size: 13px;
                border-radius: 6px;
                padding: 6px 16px;
            }
            PushButton:hover {
                background-color: rgba(239, 68, 68, 0.35);
                border: 1px solid rgba(239, 68, 68, 0.65);
                color: #ffffff;
            }
            PushButton:pressed {
                background-color: #dc2626;
                color: #ffffff;
            }
        """
    return """
        PushButton {
            background-color: rgba(239, 68, 68, 0.12);
            color: #dc2626;
            border: 1px solid rgba(239, 68, 68, 0.35);
            font-weight: 700;
            font-size: 13px;
            border-radius: 6px;
            padding: 6px 16px;
        }
        PushButton:hover {
            background-color: #dc2626;
            color: #ffffff;
            border: 1px solid #dc2626;
        }
        PushButton:pressed {
            background-color: #b91c1c;
            color: #ffffff;
        }
    """


def table_style(dark: bool | None = None) -> str:
    """Return complete TableView & TableWidget stylesheet with dark/light background and dynamic Windows accent selection."""
    is_dark = isDarkTheme() if dark is None else dark
    accent = ThemeTokens.ACTIVE_ACCENT
    sel_bg = "rgba(0, 120, 212, 0.22)" if is_dark else "rgba(0, 120, 212, 0.12)"

    if is_dark:
        return f"""
            QTableView, TableView, QTableWidget, TableWidget {{
                background-color: {ThemeTokens.DARK_TABLE_BG};
                border: 1px solid {ThemeTokens.DARK_TABLE_BORDER};
                border-radius: 8px;
                gridline-color: {ThemeTokens.DARK_TABLE_GRID};
                color: {ThemeTokens.DARK_TABLE_TEXT};
                font-family: 'Consolas', 'Cascadia Code', 'Segoe UI', monospace;
                font-size: 12px;
                selection-background-color: {sel_bg};
                selection-color: {accent};
                outline: none;
            }}
            QTableView::item, TableView::item, QTableWidget::item, TableWidget::item {{
                padding: 6px 10px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.04);
                color: {ThemeTokens.DARK_TABLE_TEXT};
            }}
            QTableView::item:selected, TableView::item:selected, QTableWidget::item:selected, TableWidget::item:selected {{
                background-color: {sel_bg};
                color: {accent};
                font-weight: 600;
            }}
            QHeaderView, QHeaderView::section {{
                background-color: {ThemeTokens.DARK_TABLE_HEADER_BG};
                color: {ThemeTokens.DARK_TEXT_MUTED};
                font-weight: 600;
                font-size: 12px;
                border: none;
                border-bottom: 1px solid {ThemeTokens.DARK_TABLE_BORDER};
                border-right: 1px solid rgba(255, 255, 255, 0.04);
                padding: 6px 10px;
            }}
            QTableCornerButton::section {{
                background-color: {ThemeTokens.DARK_TABLE_HEADER_BG};
                border: none;
                border-bottom: 1px solid {ThemeTokens.DARK_TABLE_BORDER};
            }}
            QScrollBar:vertical {{
                background: transparent;
                width: 8px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: rgba(255, 255, 255, 0.15);
                border-radius: 4px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: rgba(255, 255, 255, 0.25);
            }}
        """
    return f"""
        QTableView, TableView, QTableWidget, TableWidget {{
            background-color: {ThemeTokens.LIGHT_TABLE_BG};
            border: 1px solid {ThemeTokens.LIGHT_TABLE_BORDER};
            border-radius: 8px;
            gridline-color: {ThemeTokens.LIGHT_TABLE_GRID};
            color: {ThemeTokens.LIGHT_TABLE_TEXT};
            font-family: 'Consolas', 'Cascadia Code', 'Segoe UI', monospace;
            font-size: 12px;
            selection-background-color: {sel_bg};
            selection-color: {accent};
            outline: none;
        }}
        QTableView::item, TableView::item, QTableWidget::item, TableWidget::item {{
            padding: 6px 10px;
            border-bottom: 1px solid rgba(0, 0, 0, 0.04);
            color: {ThemeTokens.LIGHT_TABLE_TEXT};
        }}
        QTableView::item:selected, TableView::item:selected, QTableWidget::item:selected, TableWidget::item:selected {{
            background-color: {sel_bg};
            color: {accent};
            font-weight: 600;
        }}
        QHeaderView, QHeaderView::section {{
            background-color: {ThemeTokens.LIGHT_TABLE_HEADER_BG};
            color: {ThemeTokens.LIGHT_TEXT_MUTED};
            font-weight: 600;
            font-size: 12px;
            border: none;
            border-bottom: 1px solid {ThemeTokens.LIGHT_TABLE_BORDER};
            border-right: 1px solid rgba(0, 0, 0, 0.04);
            padding: 6px 10px;
        }}
        QTableCornerButton::section {{
            background-color: {ThemeTokens.LIGHT_TABLE_HEADER_BG};
            border: none;
            border-bottom: 1px solid {ThemeTokens.LIGHT_TABLE_BORDER};
        }}
        QScrollBar:vertical {{
            background: transparent;
            width: 8px;
            margin: 0px;
        }}
        QScrollBar::handle:vertical {{
            background: rgba(0, 0, 0, 0.15);
            border-radius: 4px;
            min-height: 20px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: rgba(0, 0, 0, 0.25);
        }}
    """


def key_badge_style(dark: bool | None = None, is_capturing: bool = False) -> str:
    """Return hotkey keycap badge stylesheet with dynamic accent color."""
    accent = ThemeTokens.ACTIVE_ACCENT
    if is_capturing:
        return f"""
            QLabel {{
                background-color: rgba(0, 120, 212, 0.15);
                border: 1px dashed {accent};
                border-radius: 6px;
                padding: 4px 10px;
                font-weight: 700;
                font-size: 11px;
                color: {accent};
            }}
        """
    is_dark = isDarkTheme() if dark is None else dark
    if is_dark:
        return """
            QLabel {
                background-color: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-bottom: 2px solid rgba(255, 255, 255, 0.25);
                border-radius: 6px;
                padding: 4px 10px;
                font-family: 'Segoe UI', 'Consolas', sans-serif;
                font-weight: 700;
                font-size: 12px;
                color: #f1f5f9;
            }
        """
    return """
        QLabel {
            background-color: rgba(0, 0, 0, 0.05);
            border: 1px solid rgba(0, 0, 0, 0.12);
            border-bottom: 2px solid rgba(0, 0, 0, 0.22);
            border-radius: 6px;
            padding: 4px 10px;
            font-family: 'Segoe UI', 'Consolas', sans-serif;
            font-weight: 700;
            font-size: 12px;
            color: #0f172a;
        }
    """


def capture_button_style(dark: bool | None = None, is_capturing: bool = False) -> str:
    """Return keybind capture icon button stylesheet matching keycap badge height."""
    is_dark = isDarkTheme() if dark is None else dark
    if is_capturing:
        if is_dark:
            return """
                ToolButton, PushButton {
                    background-color: rgba(14, 165, 233, 0.18);
                    border: 1px solid #0ea5e9;
                    border-radius: 6px;
                    padding: 0px;
                }
                ToolButton:hover, PushButton:hover {
                    background-color: rgba(14, 165, 233, 0.32);
                    border: 1px solid #38bdf8;
                }
                ToolButton:pressed, PushButton:pressed {
                    background-color: rgba(14, 165, 233, 0.12);
                }
            """
        return """
            ToolButton, PushButton {
                background-color: rgba(2, 132, 199, 0.12);
                border: 1px solid #0284c7;
                border-radius: 6px;
                padding: 0px;
            }
            ToolButton:hover, PushButton:hover {
                background-color: rgba(2, 132, 199, 0.22);
                border: 1px solid #0369a1;
            }
            ToolButton:pressed, PushButton:pressed {
                background-color: rgba(2, 132, 199, 0.08);
            }
        """
    if is_dark:
        return """
            ToolButton, PushButton {
                background-color: rgba(255, 255, 255, 0.06);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 6px;
                padding: 0px;
            }
            ToolButton:hover, PushButton:hover {
                background-color: rgba(255, 255, 255, 0.12);
                border: 1px solid rgba(255, 255, 255, 0.22);
            }
            ToolButton:pressed, PushButton:pressed {
                background-color: rgba(255, 255, 255, 0.04);
            }
        """
    return """
        ToolButton, PushButton {
            background-color: rgba(0, 0, 0, 0.04);
            border: 1px solid rgba(0, 0, 0, 0.12);
            border-radius: 6px;
            padding: 0px;
        }
        ToolButton:hover, PushButton:hover {
            background-color: rgba(0, 0, 0, 0.08);
            border: 1px solid rgba(0, 0, 0, 0.22);
        }
        ToolButton:pressed, PushButton:pressed {
            background-color: rgba(0, 0, 0, 0.02);
        }
    """


def status_badge_config(state: str, dark: bool | None = None) -> dict[str, str | bool]:
    """Get theme-aware status badge styling parameters."""
    is_dark = isDarkTheme() if dark is None else dark
    st = state.upper()

    if is_dark:
        configs = {
            "IDLE": {
                "label": "IDLE",
                "bg": "rgba(255, 255, 255, 0.06)",
                "border": "rgba(255, 255, 255, 0.14)",
                "dot_color": "#94a3b8",
                "text_color": "#cbd5e1",
            },
            "RECORDING": {
                "label": "RECORDING",
                "bg": "rgba(239, 68, 68, 0.18)",
                "border": "rgba(239, 68, 68, 0.45)",
                "dot_color": "#ef4444",
                "text_color": "#f87171",
            },
            "PLAYING": {
                "label": "PLAYING MACRO",
                "bg": "rgba(16, 185, 129, 0.18)",
                "border": "rgba(16, 185, 129, 0.45)",
                "dot_color": "#10b981",
                "text_color": "#34d399",
            },
            "CLICKING": {
                "label": "AUTO-CLICKING",
                "bg": "rgba(245, 158, 11, 0.18)",
                "border": "rgba(245, 158, 11, 0.45)",
                "dot_color": "#f59e0b",
                "text_color": "#fbbf24",
            },
        }
    else:
        configs = {
            "IDLE": {
                "label": "IDLE",
                "bg": "rgba(0, 0, 0, 0.06)",
                "border": "rgba(0, 0, 0, 0.12)",
                "dot_color": "#64748b",
                "text_color": "#334155",
            },
            "RECORDING": {
                "label": "RECORDING",
                "bg": "rgba(239, 68, 68, 0.12)",
                "border": "rgba(239, 68, 68, 0.35)",
                "dot_color": "#dc2626",
                "text_color": "#b91c1c",
            },
            "PLAYING": {
                "label": "PLAYING MACRO",
                "bg": "rgba(16, 185, 129, 0.12)",
                "border": "rgba(16, 185, 129, 0.35)",
                "dot_color": "#059669",
                "text_color": "#047857",
            },
            "CLICKING": {
                "label": "AUTO-CLICKING",
                "bg": "rgba(245, 158, 11, 0.12)",
                "border": "rgba(245, 158, 11, 0.35)",
                "dot_color": "#d97706",
                "text_color": "#b45309",
            },
        }

    return configs.get(st, configs["IDLE"])


def get_text_colors(dark: bool | None = None) -> dict[str, str]:
    """Return dictionary of theme text colors with dynamic Windows accent."""
    is_dark = isDarkTheme() if dark is None else dark
    accent = ThemeTokens.ACTIVE_ACCENT
    if is_dark:
        return {
            "primary": ThemeTokens.DARK_TEXT_PRIMARY,
            "secondary": ThemeTokens.DARK_TEXT_SECONDARY,
            "muted": ThemeTokens.DARK_TEXT_MUTED,
            "dim": ThemeTokens.DARK_TEXT_DIM,
            "accent": accent,
        }
    return {
        "primary": ThemeTokens.LIGHT_TEXT_PRIMARY,
        "secondary": ThemeTokens.LIGHT_TEXT_SECONDARY,
        "muted": ThemeTokens.LIGHT_TEXT_MUTED,
        "dim": ThemeTokens.LIGHT_TEXT_DIM,
        "accent": accent,
    }
