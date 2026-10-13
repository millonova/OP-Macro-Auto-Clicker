# OP Macro & Auto Clicker

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11-informational.svg)](https://www.microsoft.com/windows)
[![UI Framework](https://img.shields.io/badge/UI-PyQt6%20Fluent%20Design-blueviolet.svg)](https://riverbankcomputing.com/software/pyqt/)

**OP Macro & Auto Clicker** is a modern, high-precision desktop macro recorder, playback engine, and customizable auto-clicker built for Windows 10 and 11. Designed with Windows 11 Fluent Design principles, it offers sub-millisecond accuracy, portable JSON recording formats, and a clean user experience.

---

## Features

### Precision Macro Recorder
* **Full Input Capture**: Records keyboard presses, releases, mouse coordinates, clicks, and scroll wheel ticks.

### Precision Player
* **Speed Scaling**: Seamlessly speed up or slow down execution from `0.1x` to `10.0x`.
* **Repeat & Loop Control**: Execute once, repeat *N* times, or loop continuously until stopped.
* **Humanized Jitter**: Optional randomized micro-delays between actions to mimic natural human interactions.
* **Coordinate Smoothing**: Replays mouse path curves smoothly across displays.

### Integrated High-Speed Auto Clicker
* **Custom Click Rates**: Set custom clicks-per-second (CPS) or millisecond intervals.
* **Multi-Button Support**: Left, Right, or Middle mouse button automation.
* **Click Modes**: Single-click, double-click, and hold-down modes.
* **Dynamic Target Position**: Click at current cursor location or lock onto fixed screen coordinates.

---

## Requirements

* **OS**: Windows 10 / Windows 11 (64-bit)
* **Python**: Python 3.10+
* **Dependencies**:
  * `PyQt6` (Fluent UI application framework)
  * `pynput` (Global keyboard & mouse input hook engine)

---

## Installation & Quick Start

1. **Clone the repository**:
   ```bash
   git clone https://github.com/millonova/OP-Macro-Auto-Clicker.git
   cd OP-Macro-Auto-Clicker
   ```

2. **Set up a virtual environment (optional but recommended)**:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

3. **Install required packages**:
   ```powershell
   pip install -r requirements.txt
   ```

4. **Run OP Macro & Auto Clicker**:
   ```powershell
   python macro_plus.py
   ```

---

## Usage Guide

### 1. Recording a Macro
1. Open OP Macro & Auto Clicker and navigate to the **Recorder** tab.
2. Select whether to include mouse movements, mouse clicks, or keyboard strokes.
3. Click **Start Recording** (or press the global recording hotkey `F9`).
4. Perform your desired actions.
5. Click **Stop Recording** (`F9`).
6. Give your recording a name and click **Save**. It will be saved into the `recordings/` directory as a JSON file.

### 2. Playing Back a Macro
1. Switch to the **Playback** tab and select your saved recording.
2. Configure your replay parameters (Speed Multiplier, Loop Count, Delay Jitter).
3. Press **Play** (or press hotkey `F10`) to start playback.
4. Press `F12` at any time for emergency playback stop (**Panic Key**).

### 3. Using the Auto Clicker
1. Navigate to the **Auto Clicker** tab.
2. Choose your click interval or target CPS (Clicks Per Second).
3. Choose the mouse button (Left / Right / Middle) and click type.
4. Toggle the Auto Clicker with `F6`.

---

## Project Structure

```
OP-Macro-Auto-Clicker/
├── macro_plus.py         # Application entry point
├── macro_engine.py       # Core recording, playback, and clicking engine
├── requirements.txt      # Python dependencies
├── LICENSE               # MIT License
├── README.md             # Documentation
├── recordings/           # Directory where JSON macro profiles are stored
├── settings/             # User settings and window preferences
└── ui/                   # PyQt6 Fluent UI components
    ├── app_window.py     # Main application window
    ├── theme.py          # Fluent theme styling and color tokens
    ├── components/       # Custom buttons, sliders, and cards
    ├── models/           # Data models for macro events
    └── views/            # Recorder, Playback, and Auto Clicker views
```

---

## License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details. Free for personal, commercial, and open-source use.

---

## ⚠️ Disclaimer

OP Macro & Auto Clicker is intended for productivity automation, accessibility testing, and repetitive desktop workflows. Please follow the rules and terms of service of any software or games where you use automated input tools.
