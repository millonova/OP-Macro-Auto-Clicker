"""Macro Plus Core Engine
"""

from __future__ import annotations

import ctypes
import json
import os
import random
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from pynput import keyboard, mouse
from PyQt6.QtCore import QObject, pyqtSignal

IS_WINDOWS = sys.platform == "win32"
if IS_WINDOWS:
    try:
        winmm = ctypes.windll.winmm
        user32 = ctypes.windll.user32

        def enable_high_res_timer() -> None:
            """Request 1ms timer resolution from the Windows multimedia system."""
            winmm.timeBeginPeriod(1)

        def disable_high_res_timer() -> None:
            """Release 1ms timer resolution."""
            winmm.timeEndPeriod(1)
    except Exception:
        IS_WINDOWS = False

        def enable_high_res_timer() -> None:
            pass

        def disable_high_res_timer() -> None:
            pass
else:
    def enable_high_res_timer() -> None:
        pass

    def disable_high_res_timer() -> None:
        pass


# Win32 mouse event flag constants
WIN32_MOUSE_FLAGS = {
    "left": (0x0002, 0x0004),      # MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP
    "right": (0x0008, 0x0010),     # MOUSEEVENTF_RIGHTDOWN, MOUSEEVENTF_RIGHTUP
    "middle": (0x0020, 0x0040),    # MOUSEEVENTF_MIDDLEDOWN, MOUSEEVENTF_MIDDLEUP
}

APP_DIR = Path(__file__).resolve().parent
RECORDINGS_DIR = APP_DIR / "recordings"
SETTINGS_DIR = APP_DIR / "settings"
SETTINGS_FILE = SETTINGS_DIR / "macro_plus_settings.json"
FORMAT_VERSION = 1
MAX_ACTION_BUFFER_SIZE = 1_000_000

HOTKEY_SUGGESTIONS = (
    *(f"F{number}" for number in range(1, 13)), "Ctrl+1", "Ctrl+2", "Ctrl+3",
    "Ctrl+Shift+1", "Ctrl+Shift+2", "Insert", "Pause", "Home", "End",
)

DEFAULTS = {
    "record_hotkey": "F6",
    "play_hotkey": "F8",
    "clicker_hotkey": "F9",
    "panic_hotkey": "F12",
    "force_exit_hotkey": "F11",
    "record_moves": True,
    "move_distance": "4",
    "move_interval": "20",
    "repeat_mode": "count",
    "repeat_count": "1",
    "repeat_duration": "60",
    "playback_speed": "1.0",
    "click_interval": "100",
    "click_jitter": "0",
    "click_limit": "0",
    "click_button": "left",
    "click_location": "cursor",
    "fixed_x": "0",
    "fixed_y": "0",
    "always_on_top": False,
}


def encode_key(key: keyboard.Key | keyboard.KeyCode) -> dict[str, str]:
    """Turn a pynput key into a portable JSON object."""
    if isinstance(key, keyboard.KeyCode):
        if key.char is not None:
            return {"kind": "char", "value": key.char}
        if key.vk is not None:
            return {"kind": "vk", "value": str(key.vk)}
    return {"kind": "key", "value": key.name}


def decode_key(data: dict[str, str]) -> keyboard.Key | keyboard.KeyCode:
    kind, value = data.get("kind", "key"), data.get("value", "")
    if kind == "char":
        return keyboard.KeyCode.from_char(value)
    if kind == "vk":
        return keyboard.KeyCode.from_vk(int(value))
    return keyboard.Key[value]


def decode_button(name: str) -> mouse.Button:
    return mouse.Button[name]


MODIFIER_LABELS = {
    keyboard.Key.ctrl: "Ctrl", keyboard.Key.ctrl_l: "Ctrl", keyboard.Key.ctrl_r: "Ctrl",
    keyboard.Key.shift: "Shift", keyboard.Key.shift_l: "Shift", keyboard.Key.shift_r: "Shift",
    keyboard.Key.alt: "Alt", keyboard.Key.alt_l: "Alt", keyboard.Key.alt_r: "Alt", keyboard.Key.alt_gr: "Alt",
    keyboard.Key.cmd: "Win", keyboard.Key.cmd_l: "Win", keyboard.Key.cmd_r: "Win",
}


def normalise_hotkey(text: str) -> str:
    """Convert friendly input such as ``Ctrl+1`` or ``Ctrl+Alt+X`` into pynput hotkey syntax."""
    aliases = {
        "ctrl": "ctrl", "control": "ctrl", "shift": "shift", "alt": "alt",
        "win": "cmd", "windows": "cmd", "cmd": "cmd", "escape": "esc", "esc": "esc",
        "enter": "enter", "return": "enter", "tab": "tab", "space": "space",
        "insert": "insert", "ins": "insert", "delete": "delete", "del": "delete",
        "home": "home", "end": "end", "pageup": "page_up", "pagedown": "page_down",
        "page_up": "page_up", "page_down": "page_down", "pause": "pause",
        "up": "up", "down": "down", "left": "left", "right": "right"
    }
    parts = [part.strip() for part in text.split("+")]
    if not parts or any(not part for part in parts):
        raise ValueError("Enter a valid key combination (e.g. F6 or Ctrl+1).")
    normalised: list[str] = []
    for part in parts:
        lower = part.casefold()
        if lower.startswith("<") and lower.endswith(">"):
            normalised.append(lower)
        elif lower in aliases:
            normalised.append(f"<{aliases[lower]}>")
        elif lower.startswith("f") and lower[1:].isdigit() and 1 <= int(lower[1:]) <= 24:
            normalised.append(f"<{lower}>")
        elif lower in {"insert", "pause", "home", "end", "esc", "tab", "space", "enter", "delete", "page_up", "page_down", "up", "down", "left", "right"}:
            normalised.append(f"<{lower}>")
        elif len(part) == 1:
            normalised.append(lower)
        else:
            raise ValueError(f"'{part}' is not a supported key name.")
    return "+".join(normalised)


def captured_key_label(key: keyboard.Key | keyboard.KeyCode) -> str | None:
    """Return a user-friendly label for a physically pressed key."""
    if key in MODIFIER_LABELS:
        return MODIFIER_LABELS[key]

    # Virtual Key code mapping (Windows / platform standard)
    if isinstance(key, keyboard.KeyCode):
        if key.vk is not None:
            if 65 <= key.vk <= 90:
                return chr(key.vk)  # A-Z
            if 48 <= key.vk <= 57:
                return chr(key.vk)  # 0-9
            if 96 <= key.vk <= 105:
                return str(key.vk - 96)  # Numpad 0-9
            if 112 <= key.vk <= 135:
                return f"F{key.vk - 111}"  # F1-F24

        if key.char:
            # Handle Ctrl+letter ASCII control characters (1-26 -> A-Z)
            if 1 <= ord(key.char) <= 26:
                return chr(ord(key.char) + 64)
            if key.char.isprintable() and not key.char.isspace():
                return key.char.upper()
        return None

    if hasattr(key, "name") and key.name:
        lower = key.name.lower()
        if lower.startswith("f") and lower[1:].isdigit():
            return key.name.upper()
        name_map = {
            "cmd": "Win", "esc": "Esc", "space": "Space", "enter": "Enter",
            "return": "Enter", "tab": "Tab", "delete": "Delete", "insert": "Insert",
            "home": "Home", "end": "End", "page_up": "PageUp", "page_down": "PageDown",
            "up": "Up", "down": "Down", "left": "Left", "right": "Right", "pause": "Pause",
            "backspace": "Backspace"
        }
        return name_map.get(lower, key.name.title())
    return None


class EngineSignals(QObject):
    """Thread-safe signals connecting the core backend engine to the PyQt6 UI."""
    status_changed = pyqtSignal(str)
    state_changed = pyqtSignal(str)  # "IDLE", "RECORDING", "PLAYING", "CLICKING"
    recording_progress = pyqtSignal(int, float)  # (action_count, current_duration) at 30 FPS max
    actions_updated = pyqtSignal(list, float)  # (full_actions_snapshot, total_duration) on finish/import
    playback_finished = pyqtSignal(bool, str)  # (was_stopped, message)
    clicker_finished = pyqtSignal(bool, int)  # (was_stopped, click_count)
    clicker_progress = pyqtSignal(int)  # (current_click_count)
    hotkey_captured = pyqtSignal(str, str)  # (target_action, formatted_hotkey)
    hotkey_conflict = pyqtSignal(str, str)  # (target_action, conflicted_hotkey)
    hotkey_capture_cancelled = pyqtSignal()
    notification_requested = pyqtSignal(str, str, str)  # (severity, title, message)


class MacroEngine:
    """Thread-safe global input recorder, precision player, and auto clicker engine."""

    def __init__(self) -> None:
        self.signals = EngineSignals()
        self.lock = threading.RLock()

        try:
            RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)
            SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass

        self.settings: dict[str, Any] = self.load_settings()
        self.actions: list[dict] = []

        # State flags
        self.recording = False
        self.playing = False
        self.clicking = False
        self.record_started = 0.0
        self.last_move_time = 0.0
        self.last_move_position: tuple[int, int] | None = None
        self.active_record_moves = True
        self.active_move_distance = 4
        self.active_move_interval = 0.02
        self._last_rec_progress_emit = 0.0

        # Thread synchronization events
        self.play_stop = threading.Event()
        self.clicker_stop = threading.Event()

        # Hotkeys
        self.hotkey_bindings: list[keyboard.HotKey] = []
        self.hotkey_components: set[keyboard.Key | keyboard.KeyCode] = set()
        self.capture_target: str | None = None
        self.capture_pressed: set[keyboard.Key | keyboard.KeyCode] = set()
        self.hotkeys_guarded = False

        self.current_filename = "my_macro"

        # Worker threads tracking
        self._playback_thread: threading.Thread | None = None
        self._clicker_thread: threading.Thread | None = None

        # Listeners
        self.keyboard_listener: keyboard.Listener | None = None
        self.mouse_listener: mouse.Listener | None = None
        self.start_listeners()

        self.apply_hotkeys(quiet=True)

    def start_listeners(self) -> None:
        """Start global keyboard and mouse hooks as non-blocking daemon threads."""
        with self.lock:
            self.stop_listeners()
            try:
                self.keyboard_listener = keyboard.Listener(
                    on_press=self._safe_on_key_press,
                    on_release=self._safe_on_key_release,
                    daemon=True
                )
                self.mouse_listener = mouse.Listener(
                    on_move=self._safe_on_mouse_move,
                    on_click=self._safe_on_mouse_click,
                    on_scroll=self._safe_on_mouse_scroll,
                    daemon=True
                )
                self.keyboard_listener.start()
                self.mouse_listener.start()
            except Exception as exc:
                self.signals.status_changed.emit(f"Failed to initialize input listeners: {exc}")

    def stop_listeners(self) -> None:
        """Gracefully terminate listeners."""
        with self.lock:
            if self.keyboard_listener and self.keyboard_listener.is_alive():
                try:
                    self.keyboard_listener.stop()
                except Exception:
                    pass
            if self.mouse_listener and self.mouse_listener.is_alive():
                try:
                    self.mouse_listener.stop()
                except Exception:
                    pass
            self.keyboard_listener = None
            self.mouse_listener = None

    @staticmethod
    def load_settings() -> dict[str, Any]:
        settings = DEFAULTS.copy()
        if SETTINGS_FILE.exists():
            try:
                content = SETTINGS_FILE.read_text(encoding="utf-8")
                stored = json.loads(content)
                if isinstance(stored, dict):
                    settings.update({k: v for k, v in stored.items() if k in settings})
            except (OSError, IOError, json.JSONDecodeError, UnicodeDecodeError, TypeError):
                pass
        return settings

    def save_settings(self) -> bool:
        with self.lock:
            try:
                SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
                temp_file = SETTINGS_FILE.with_suffix(".tmp")
                temp_file.write_text(json.dumps(self.settings, indent=2), encoding="utf-8")
                temp_file.replace(SETTINGS_FILE)
                return True
            except (OSError, IOError) as exc:
                self.signals.status_changed.emit(f"Could not save settings: {exc}")
                return False

    def update_setting(self, key: str, value: Any, auto_save: bool = True) -> None:
        with self.lock:
            self.settings[key] = value
            if auto_save:
                self.save_settings()

    def get_state(self) -> str:
        with self.lock:
            if self.recording:
                return "RECORDING"
            if self.playing:
                return "PLAYING"
            if self.clicking:
                return "CLICKING"
            return "IDLE"

    def emit_state_update(self) -> None:
        state = self.get_state()
        self.signals.state_changed.emit(state)

    def apply_hotkeys(self, quiet: bool = False) -> bool:
        with self.lock:
            values = {
                "record": str(self.settings.get("record_hotkey", DEFAULTS["record_hotkey"])),
                "play": str(self.settings.get("play_hotkey", DEFAULTS["play_hotkey"])),
                "clicker": str(self.settings.get("clicker_hotkey", DEFAULTS["clicker_hotkey"])),
                "stop_all": str(self.settings.get("panic_hotkey", DEFAULTS["panic_hotkey"])),
                "force_exit": str(self.settings.get("force_exit_hotkey", DEFAULTS["force_exit_hotkey"])),
            }
            try:
                parsed = {command: keyboard.HotKey.parse(normalise_hotkey(label)) for command, label in values.items()}
                signatures = {frozenset(keys) for keys in parsed.values()}
                if len(signatures) != len(values):
                    raise ValueError("Every action needs a unique hotkey.")
            except (KeyError, ValueError) as exc:
                if not quiet:
                    self.signals.notification_requested.emit("error", "Invalid Hotkey", str(exc))
                return False

            self.hotkey_components = set().union(*parsed.values())
            self.hotkey_bindings = [
                keyboard.HotKey(keys, lambda action=command: self.activate_hotkey(action))
                for command, keys in parsed.items()
            ]
            self.save_settings()
            if not quiet:
                self.signals.status_changed.emit("Global hotkeys applied and saved.")
                self.signals.notification_requested.emit("success", "Hotkeys Saved", "Global hotkeys successfully updated.")
            return True

    def set_guarded(self, guarded: bool) -> None:
        """Enable or disable global macro/clicker hotkey guard (e.g. while in Settings view)."""
        with self.lock:
            self.hotkeys_guarded = guarded

    def activate_hotkey(self, command: str) -> None:
        """Run on pynput listener thread when a hotkey triggers. Dispatches safely."""
        # Emergency aborts always execute regardless of view state
        if command == "force_exit":
            self.force_exit()
            return
        if command == "stop_all":
            self.stop_all()
            return

        with self.lock:
            if self.hotkeys_guarded:
                self.signals.status_changed.emit("Global macro execution triggers are guarded while viewing Settings.")
                return

        if command == "record":
            self.toggle_recording()
        elif command == "play":
            self.toggle_playback()
        elif command == "clicker":
            self.toggle_clicker()

    def arm_hotkey_capture(self, target: str) -> None:
        with self.lock:
            self.capture_target = target
            self.capture_pressed.clear()
            self.signals.status_changed.emit("Press desired key combination (e.g. F6, Ctrl+1). Press Esc to cancel.")

    def finish_hotkey_capture(self, target: str, hotkey: str) -> bool:
        with self.lock:
            setting_map = {
                "record": "record_hotkey",
                "play": "play_hotkey",
                "clicker": "clicker_hotkey",
                "stop_all": "panic_hotkey",
                "force_exit": "force_exit_hotkey",
            }
            key_name = setting_map.get(target)
            if not key_name:
                return False

            previous = self.settings.get(key_name)
            self.settings[key_name] = hotkey

            if self.apply_hotkeys(quiet=True):
                self.capture_target = None
                self.capture_pressed.clear()
                self.signals.status_changed.emit(f"{hotkey} assigned successfully.")
                self.signals.hotkey_captured.emit(target, hotkey)
                self.signals.notification_requested.emit("success", "Hotkey Updated", f"{hotkey} assigned to {target}.")
                return True
            else:
                self.settings[key_name] = previous
                self.apply_hotkeys(quiet=True)
                # Keep capture armed so user can immediately press another key combination
                self.capture_target = target
                self.capture_pressed.clear()
                self.signals.status_changed.emit(f"'{hotkey}' is already in use. Press a different key combination or Esc to cancel.")
                self.signals.notification_requested.emit("warning", "Hotkey Conflict", f"'{hotkey}' is already used by another action. Choose another key.")
                self.signals.hotkey_conflict.emit(target, hotkey)
                return False

    def _safe_on_key_press(self, key: keyboard.Key | keyboard.KeyCode) -> None:
        try:
            self.on_key_press(key)
        except Exception:
            pass

    def _safe_on_key_release(self, key: keyboard.Key | keyboard.KeyCode) -> None:
        try:
            self.on_key_release(key)
        except Exception:
            pass

    def _safe_on_mouse_move(self, x: int, y: int) -> None:
        try:
            self.on_mouse_move(x, y)
        except Exception:
            pass

    def _safe_on_mouse_click(self, x: int, y: int, button: mouse.Button, pressed: bool) -> None:
        try:
            self.on_mouse_click(x, y, button, pressed)
        except Exception:
            pass

    def _safe_on_mouse_scroll(self, x: int, y: int, dx: int, dy: int) -> None:
        try:
            self.on_mouse_scroll(x, y, dx, dy)
        except Exception:
            pass

    def on_key_press(self, key: keyboard.Key | keyboard.KeyCode) -> None:
        with self.lock:
            # Hotkey capture handling
            if self.capture_target is not None:
                if key == keyboard.Key.esc:
                    self.capture_target = None
                    self.capture_pressed.clear()
                    self.signals.status_changed.emit("Hotkey capture cancelled.")
                    self.signals.hotkey_capture_cancelled.emit()
                    return

                # If modifier key (Ctrl, Shift, Alt, Win), record as held and wait for trigger key
                if key in MODIFIER_LABELS:
                    self.capture_pressed.add(key)
                    held_mods = [MODIFIER_LABELS[m] for m in self.capture_pressed if m in MODIFIER_LABELS]
                    ordered = [m for m in ("Ctrl", "Shift", "Alt", "Win") if m in held_mods]
                    if ordered:
                        self.signals.status_changed.emit(f"Holding: {' + '.join(ordered)} + ... (Press key to complete)")
                    return

                # Non-modifier trigger key pressed
                label = captured_key_label(key)
                if label is None:
                    return

                modifiers = [MODIFIER_LABELS[m] for m in self.capture_pressed if m in MODIFIER_LABELS]
                ordered_modifiers = [name for name in ("Ctrl", "Shift", "Alt", "Win") if name in modifiers]
                target = self.capture_target
                self.capture_target = None
                self.capture_pressed.clear()
                hotkey = "+".join((*ordered_modifiers, label))
                self.finish_hotkey_capture(target, hotkey)
                return

            if self.keyboard_listener:
                canonical = self.keyboard_listener.canonical(key)
                for hotkey in self.hotkey_bindings:
                    hotkey.press(canonical)
                if canonical in self.hotkey_components:
                    return

            if self.recording and not self.playing and not self.clicking:
                self.add_action("key_down", {"key": encode_key(key)})

    def on_key_release(self, key: keyboard.Key | keyboard.KeyCode) -> None:
        with self.lock:
            if self.capture_target is not None:
                self.capture_pressed.discard(key)
                if key in MODIFIER_LABELS:
                    mod_name = MODIFIER_LABELS[key]
                    self.capture_pressed = {k for k in self.capture_pressed if MODIFIER_LABELS.get(k) != mod_name}
                return

            if self.keyboard_listener:
                canonical = self.keyboard_listener.canonical(key)
                for hotkey in self.hotkey_bindings:
                    hotkey.release(canonical)
                if canonical in self.hotkey_components:
                    return

            if self.recording and not self.playing and not self.clicking:
                self.add_action("key_up", {"key": encode_key(key)})

    def on_mouse_move(self, x: int, y: int) -> None:
        if not self.recording or self.playing or self.clicking or not self.active_record_moves:
            return

        now = time.perf_counter()
        previous = self.last_move_position
        if previous is not None:
            # Adaptive distance & interval throttling
            close = abs(x - previous[0]) < self.active_move_distance and abs(y - previous[1]) < self.active_move_distance
            if close or (now - self.last_move_time) < self.active_move_interval:
                return

        self.last_move_position = (x, y)
        self.last_move_time = now
        self.add_action("mouse_move", {"x": int(x), "y": int(y)})

    def on_mouse_click(self, x: int, y: int, button: mouse.Button, pressed: bool) -> None:
        if self.recording and not self.playing and not self.clicking:
            self.add_action("mouse_down" if pressed else "mouse_up", {"x": int(x), "y": int(y), "button": button.name})

    def on_mouse_scroll(self, x: int, y: int, dx: int, dy: int) -> None:
        if self.recording and not self.playing and not self.clicking:
            self.add_action("mouse_scroll", {"x": int(x), "y": int(y), "dx": int(dx), "dy": int(dy)})

    def add_action(self, action_type: str, payload: dict) -> None:
        """Fast O(1) action appending with throttled progress signal emission."""
        with self.lock:
            if not self.recording or len(self.actions) >= MAX_ACTION_BUFFER_SIZE:
                return
            t_now = time.perf_counter()
            t_offset = round(t_now - self.record_started, 6)
            self.actions.append({"time": t_offset, "type": action_type, **payload})
            action_count = len(self.actions)

            # Throttled live update (max 30 FPS = ~33ms)
            if t_now - self._last_rec_progress_emit >= 0.033:
                self._last_rec_progress_emit = t_now
                should_emit = True
            else:
                should_emit = False

        if should_emit:
            self.signals.recording_progress.emit(action_count, t_offset)

    def toggle_recording(self) -> None:
        with self.lock:
            if self.recording:
                self.stop_recording()
            else:
                self.start_recording()

    def start_recording(self) -> None:
        with self.lock:
            if self.playing or self.clicking:
                self.signals.status_changed.emit("Stop playback or auto clicker before recording.")
                self.signals.notification_requested.emit("warning", "Cannot Record", "Stop playback or auto clicker before recording.")
                return
            if self.recording:
                return

            self.actions = []
            try:
                self.active_move_distance = max(0, int(self.settings.get("move_distance", "4")))
                self.active_move_interval = max(1, int(self.settings.get("move_interval", "20"))) / 1000.0
            except ValueError:
                self.active_move_distance, self.active_move_interval = 4, 0.02

            self.active_record_moves = bool(self.settings.get("record_moves", True))
            self.record_started = time.perf_counter()
            self._last_rec_progress_emit = self.record_started
            self.last_move_time = 0.0
            self.last_move_position = None
            self.recording = True

        self.emit_state_update()
        self.signals.status_changed.emit("Recording in progress... Actions captured. Press Record hotkey or button to stop.")
        self.signals.actions_updated.emit([], 0.0)

    def stop_recording(self) -> None:
        with self.lock:
            if not self.recording:
                return
            self.recording = False
            snapshot = list(self.actions)
            duration = snapshot[-1]["time"] if snapshot else 0.0

        self.emit_state_update()
        self.signals.actions_updated.emit(snapshot, duration)
        self.signals.status_changed.emit(f"Recording finished ({len(snapshot)} actions captured). Ready to play or save.")
        self.signals.notification_requested.emit("info", "Recording Finished", f"{len(snapshot)} actions captured.")

    def clear_recording(self) -> None:
        with self.lock:
            if self.recording or self.playing:
                self.signals.status_changed.emit("Stop recording or playback before clearing actions.")
                return
            self.actions = []
        self.signals.actions_updated.emit([], 0.0)
        self.signals.status_changed.emit("Actions cleared.")

    def toggle_playback(self) -> None:
        with self.lock:
            if self.playing:
                self.stop_playback()
            else:
                self.start_playback()

    def start_playback(self) -> None:
        with self.lock:
            if self.recording:
                self.signals.status_changed.emit("Stop recording before starting playback.")
                return
            if self.playing:
                return
            actions = list(self.actions)
            if not actions:
                self.signals.status_changed.emit("No actions to play. Record or import a macro first.")
                self.signals.notification_requested.emit("warning", "No Actions", "Record or import a macro first.")
                return

            try:
                mode = str(self.settings.get("repeat_mode", "count")).lower()
                if mode not in ("count", "timer"):
                    raise ValueError("Select a valid repeat mode (count or timer).")
                speed = float(self.settings.get("playback_speed", "1.0"))
                if not 0.05 <= speed <= 10.0:
                    raise ValueError("Playback speed must be between 0.05x and 10x.")
                if mode == "count":
                    count = int(self.settings.get("repeat_count", "1"))
                    duration = 0.0
                    if count < 1:
                        raise ValueError("Repeat count must be at least 1.")
                else:
                    count = 0
                    duration = float(self.settings.get("repeat_duration", "60"))
                    if duration <= 0:
                        raise ValueError("Timer duration must be positive.")
            except ValueError as exc:
                self.signals.status_changed.emit(str(exc))
                self.signals.notification_requested.emit("error", "Playback Config Error", str(exc))
                return

            self.play_stop.clear()
            self.playing = True

        self.emit_state_update()
        mode_text = f"{count} loop(s)" if mode == "count" else f"for {duration:g} seconds"
        self.signals.status_changed.emit(f"Playback active at {speed:g}x ({mode_text}). Press Play hotkey or Stop to cancel.")

        self._playback_thread = threading.Thread(
            target=self.playback_worker,
            args=(actions, mode, count, duration, speed),
            daemon=True,
            name="MacroPlaybackWorker"
        )
        self._playback_thread.start()

    def stop_playback(self) -> None:
        with self.lock:
            if not self.playing:
                return
            self.play_stop.set()
        self.signals.status_changed.emit("Stopping playback...")

    def playback_worker(self, actions: list[dict], mode: str, count: int, duration: float, speed: float) -> None:
        controller = mouse.Controller()
        key_controller = keyboard.Controller()
        cycle = 0
        deadline = time.perf_counter() + duration
        held_keys: list[keyboard.Key | keyboard.KeyCode] = []
        held_buttons: list[str] = []
        enable_high_res_timer()

        try:
            while not self.play_stop.is_set() and (mode == "timer" or cycle < count):
                began = time.perf_counter()
                for action in actions:
                    if self.play_stop.is_set():
                        break
                    if mode == "timer" and time.perf_counter() >= deadline:
                        break

                    action_time = action.get("time", 0.0) / speed

                    # High-precision hybrid scheduling (sleep bulk, micro-wait tail)
                    while not self.play_stop.is_set():
                        now = time.perf_counter()
                        if mode == "timer" and now >= deadline:
                            break
                        remaining = action_time - (now - began)
                        if remaining <= 0:
                            break
                        if remaining > 0.003:
                            # Sleep bulk with safety margin to yield CPU completely
                            self.play_stop.wait(min(remaining - 0.0015, 0.05))
                        else:
                            # Short spin-wait with yield
                            time.sleep(0)

                    if self.play_stop.is_set() or (mode == "timer" and time.perf_counter() >= deadline):
                        break

                    self.perform_action(action, controller, key_controller, held_keys, held_buttons)

                cycle += 1
                if mode == "timer" and time.perf_counter() >= deadline:
                    break
        except Exception as exc:
            with self.lock:
                self.playing = False
            self.emit_state_update()
            self.signals.playback_finished.emit(True, f"Playback error: {exc}")
            return
        finally:
            disable_high_res_timer()
            # Cleanly release any held inputs to prevent stuck keys/buttons
            for key in reversed(held_keys):
                try:
                    key_controller.release(key)
                except Exception:
                    pass
            for btn_name in reversed(held_buttons):
                try:
                    if IS_WINDOWS:
                        up_flag = WIN32_MOUSE_FLAGS.get(btn_name, (0x0002, 0x0004))[1]
                        user32.mouse_event(up_flag, 0, 0, 0, 0)
                    else:
                        controller.release(decode_button(btn_name))
                except Exception:
                    pass

            with self.lock:
                self.playing = False
            self.emit_state_update()
            stopped = self.play_stop.is_set()
            msg = "Playback stopped." if stopped else f"Playback completed ({cycle} cycle{'s' if cycle != 1 else ''})."
            self.signals.playback_finished.emit(stopped, msg)
            self.signals.status_changed.emit(msg)

    @staticmethod
    def perform_action(action: dict, controller: mouse.Controller, key_controller: keyboard.Controller,
                       held_keys: list[keyboard.Key | keyboard.KeyCode], held_buttons: list[str]) -> None:
        kind = action.get("type", "")
        if kind == "mouse_move":
            x, y = int(action.get("x", 0)), int(action.get("y", 0))
            if IS_WINDOWS:
                user32.SetCursorPos(x, y)
            else:
                controller.position = (x, y)

        elif kind in ("mouse_down", "mouse_up"):
            x, y = int(action.get("x", 0)), int(action.get("y", 0))
            btn_name = action.get("button", "left")
            if IS_WINDOWS:
                user32.SetCursorPos(x, y)
                down_flag, up_flag = WIN32_MOUSE_FLAGS.get(btn_name, (0x0002, 0x0004))
                if kind == "mouse_down":
                    user32.mouse_event(down_flag, 0, 0, 0, 0)
                    held_buttons.append(btn_name)
                else:
                    user32.mouse_event(up_flag, 0, 0, 0, 0)
                    if btn_name in held_buttons:
                        held_buttons.remove(btn_name)
            else:
                controller.position = (x, y)
                btn = decode_button(btn_name)
                if kind == "mouse_down":
                    controller.press(btn)
                    held_buttons.append(btn_name)
                else:
                    controller.release(btn)
                    if btn_name in held_buttons:
                        held_buttons.remove(btn_name)

        elif kind == "mouse_scroll":
            x, y = int(action.get("x", 0)), int(action.get("y", 0))
            if IS_WINDOWS:
                user32.SetCursorPos(x, y)
            else:
                controller.position = (x, y)
            controller.scroll(int(action.get("dx", 0)), int(action.get("dy", 0)))

        elif kind in ("key_down", "key_up"):
            key = decode_key(action.get("key", {}))
            if kind == "key_down":
                key_controller.press(key)
                held_keys.append(key)
            else:
                key_controller.release(key)
                if key in held_keys:
                    held_keys.remove(key)

    def toggle_clicker(self) -> None:
        with self.lock:
            if self.clicking:
                self.clicker_stop.set()
                self.clicking = False
                self.emit_state_update()
                self.signals.status_changed.emit("Auto clicker stop requested.")
                return

            if self.recording or self.playing:
                self.signals.status_changed.emit("Stop recording or playback before running auto clicker.")
                self.signals.notification_requested.emit("warning", "Cannot Start Clicker", "Stop recording or playback first.")
                return

            try:
                interval_ms = float(self.settings.get("click_interval", "100"))
                if interval_ms < 0.05:
                    interval_ms = 0.1
                interval = interval_ms / 1000.0

                jitter_ms = float(self.settings.get("click_jitter", "0") or "0")
                jitter = max(0.0, jitter_ms) / 1000.0

                limit = max(0, int(self.settings.get("click_limit", "0") or "0"))
                button_name = str(self.settings.get("click_button", "left")).lower()
                if button_name not in ("left", "right", "middle"):
                    button_name = "left"

                position = None if self.settings.get("click_location", "cursor") == "cursor" else (
                    int(self.settings.get("fixed_x", "0")), int(self.settings.get("fixed_y", "0"))
                )
            except (KeyError, TypeError, ValueError):
                self.signals.status_changed.emit("Please enter valid click timing, limit, and coordinates.")
                self.signals.notification_requested.emit("error", "Config Error", "Please verify click timing and coordinates.")
                return

            self.clicker_stop.clear()
            self.clicking = True

        self.emit_state_update()
        location_desc = "current cursor" if position is None else f"fixed position {position}"
        limit_desc = "until stopped" if limit == 0 else f"for {limit} clicks"
        self.signals.status_changed.emit(f"Auto clicker active ({interval_ms:g} ms interval) at {location_desc}, {limit_desc}.")

        self._clicker_thread = threading.Thread(
            target=self.clicker_worker,
            args=(interval, jitter, limit, button_name, position),
            daemon=True,
            name="MacroClickerWorker"
        )
        self._clicker_thread.start()

    def clicker_worker(self, interval: float, jitter: float, limit: int, button_name: str,
                       position: tuple[int, int] | None) -> None:
        clicks = 0
        enable_high_res_timer()

        down_flag, up_flag = WIN32_MOUSE_FLAGS.get(button_name, (0x0002, 0x0004))
        pynput_controller = None
        pynput_button = None
        if not IS_WINDOWS:
            pynput_controller = mouse.Controller()
            pynput_button = decode_button(button_name)

        last_progress_emit = time.perf_counter()

        try:
            while not self.clicker_stop.is_set() and (limit == 0 or clicks < limit):
                t_click_start = time.perf_counter()

                # Dispatch rapid click
                if IS_WINDOWS:
                    if position is not None:
                        user32.SetCursorPos(position[0], position[1])
                    user32.mouse_event(down_flag, 0, 0, 0, 0)
                    user32.mouse_event(up_flag, 0, 0, 0, 0)
                else:
                    if position is not None:
                        pynput_controller.position = position
                    pynput_controller.click(pynput_button)
                clicks += 1

                # Throttle GUI progress update (max ~20 times/sec to prevent UI event queue overload)
                if t_click_start - last_progress_emit > 0.05:
                    self.signals.clicker_progress.emit(clicks)
                    last_progress_emit = t_click_start

                target_delay = interval + (random.uniform(0, jitter) if jitter > 0 else 0)

                # High-efficiency hybrid timing
                if target_delay > 0.002:
                    sleep_part = target_delay - 0.0012
                    if self.clicker_stop.wait(sleep_part):
                        break
                    while not self.clicker_stop.is_set() and (time.perf_counter() - t_click_start) < target_delay:
                        time.sleep(0)
                elif target_delay > 0:
                    while not self.clicker_stop.is_set() and (time.perf_counter() - t_click_start) < target_delay:
                        time.sleep(0)
        finally:
            disable_high_res_timer()
            if IS_WINDOWS:
                user32.mouse_event(up_flag, 0, 0, 0, 0)
            elif pynput_controller and pynput_button:
                try:
                    pynput_controller.release(pynput_button)
                except Exception:
                    pass

            with self.lock:
                self.clicking = False
            self.emit_state_update()
            stopped = self.clicker_stop.is_set()
            self.signals.clicker_progress.emit(clicks)
            self.signals.clicker_finished.emit(stopped, clicks)
            msg = f"Auto clicker stopped after {clicks} clicks." if stopped else f"Auto clicker finished ({clicks} clicks)."
            self.signals.status_changed.emit(msg)

    def stop_all(self) -> None:
        """Panic stop all active operations immediately."""
        with self.lock:
            was_recording = self.recording
            self.recording = False
            self.play_stop.set()
            self.clicker_stop.set()
            self.playing = False
            self.clicking = False
            snapshot = list(self.actions)
            duration = snapshot[-1]["time"] if snapshot else 0.0

        self.emit_state_update()
        if was_recording:
            self.signals.actions_updated.emit(snapshot, duration)
        self.signals.status_changed.emit("🛑 Panic Stop activated. All operations halted.")
        self.signals.notification_requested.emit("error", "Panic Stop", "All active macros and clickers were halted.")

    def force_exit(self) -> None:
        """Emergency process termination."""
        with self.lock:
            self.play_stop.set()
            self.clicker_stop.set()
            self.stop_listeners()
            disable_high_res_timer()
        os._exit(0)

    def capture_cursor(self) -> tuple[int, int]:
        if IS_WINDOWS:
            pt = (ctypes.c_long * 2)()
            user32.GetCursorPos(pt)
            x, y = int(pt[0]), int(pt[1])
        else:
            pos = mouse.Controller().position
            x, y = int(pos[0]), int(pos[1])

        with self.lock:
            self.settings["fixed_x"] = str(x)
            self.settings["fixed_y"] = str(y)
            self.settings["click_location"] = "fixed"
            self.save_settings()

        self.signals.status_changed.emit(f"Fixed click position set to ({x}, {y}).")
        return x, y

    def recording_document(self) -> dict:
        with self.lock:
            actions = list(self.actions)
        return {
            "format": "macro-plus",
            "version": FORMAT_VERSION,
            "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "actions": actions
        }

    def safe_filename(self, custom_name: str | None = None) -> str:
        name = custom_name if custom_name is not None else self.current_filename
        allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_. "
        filtered = "".join(char for char in name.strip() if char in allowed).strip(". ")
        return filtered or "macro"

    def write_json(self, destination: Path) -> None:
        with self.lock:
            if not self.actions:
                raise ValueError("There are no actions to save.")
            doc = self.recording_document()

        destination.parent.mkdir(parents=True, exist_ok=True)
        temp_dest = destination.with_suffix(".tmp")
        temp_dest.write_text(json.dumps(doc, indent=2), encoding="utf-8")
        temp_dest.replace(destination)

    def save_recording(self, file_name: str | None = None) -> Path:
        with self.lock:
            if file_name:
                self.current_filename = file_name
            dest = RECORDINGS_DIR / f"{self.safe_filename()}.json"
            self.write_json(dest)

        self.signals.status_changed.emit(f"Saved: {dest.name}")
        self.signals.notification_requested.emit("success", "Saved", f"Recording saved to {dest.name}")
        return dest

    def export_recording(self, destination_path: str) -> None:
        path = Path(destination_path)
        self.write_json(path)
        self.signals.status_changed.emit(f"Exported: {path.name}")
        self.signals.notification_requested.emit("success", "Exported", f"Exported macro to {path.name}")

    def import_recording(self, source_path: str) -> int:
        source = Path(source_path)
        if not source.exists():
            raise FileNotFoundError(f"File not found: {source.name}")

        try:
            content = source.read_text(encoding="utf-8")
            document = json.loads(content)
        except (IOError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise ValueError(f"Corrupted or invalid JSON file: {exc}")

        if not isinstance(document, dict) or "actions" not in document:
            raise ValueError("Invalid format: document must contain an 'actions' list.")

        actions = document["actions"]
        self.validate_actions_schema(actions)

        self.stop_all()
        with self.lock:
            self.actions = actions
            duration = actions[-1]["time"] if actions else 0.0
            self.current_filename = source.stem

        self.signals.actions_updated.emit(actions, duration)
        self.signals.status_changed.emit(f"Imported {len(actions)} actions from {source.name}")
        self.signals.notification_requested.emit("success", "Imported", f"Loaded {len(actions)} actions from {source.name}")
        return len(actions)

    @staticmethod
    def validate_actions_schema(actions: Any) -> None:
        """Strict validation of macro actions schema."""
        if not isinstance(actions, list):
            raise ValueError("'actions' must be a list")
        previous_time = -1.0
        valid_types = {"mouse_move", "mouse_down", "mouse_up", "mouse_scroll", "key_down", "key_up"}

        for i, action in enumerate(actions):
            if not isinstance(action, dict):
                raise ValueError(f"Action #{i + 1} must be an object/dict")
            act_type = action.get("type")
            if act_type not in valid_types:
                raise ValueError(f"Action #{i + 1} has unrecognized type '{act_type}'")

            try:
                event_time = float(action.get("time", 0.0))
            except (TypeError, ValueError):
                raise ValueError(f"Action #{i + 1} has non-numeric timestamp")

            if event_time < previous_time or event_time < 0:
                raise ValueError(f"Action #{i + 1} timestamp must be non-negative and monotonic")
            previous_time = event_time

            if act_type.startswith("mouse_"):
                if "x" not in action or "y" not in action:
                    raise ValueError(f"Action #{i + 1} missing x or y coordinate")
                int(action["x"])
                int(action["y"])

            if act_type in ("mouse_down", "mouse_up"):
                if "button" not in action or action["button"] not in ("left", "right", "middle"):
                    raise ValueError(f"Action #{i + 1} missing or invalid mouse button")

            if act_type == "mouse_scroll":
                int(action.get("dx", 0))
                int(action.get("dy", 0))

            if act_type.startswith("key_"):
                key_obj = action.get("key")
                if not isinstance(key_obj, dict) or "value" not in key_obj or "kind" not in key_obj:
                    raise ValueError(f"Action #{i + 1} has invalid key object format")

    def shutdown(self) -> None:
        """Clean shutdown of threads and timers."""
        self.stop_all()
        self.save_settings()
        self.stop_listeners()
        disable_high_res_timer()
