# Move Me - AI Coding Instructions

## Project Overview

Move Me is a cross-platform break reminder tool built with Python 3.13+ that automatically shows fullscreen overlays at configurable intervals to encourage healthy work breaks. The architecture emphasizes async programming, platform abstraction, GUI overlays, and state persistence.

## Development Environment

-   **Package Manager**: `uv` (not pip/poetry) - always use `uv run`, `uv add`, `uv sync`
-   **Python Version**: 3.13+ (see `.python-version`)
-   **Entry Point**: `move_me.main:app` (Typer CLI) via `uv run move-me main`
-   **Dependencies**: typer, plyer, pyyaml, psutil, tkinter (see `pyproject.toml`)

## Core Architecture

### Essential Components

1. **TimerManager** (`move_me/core/timer.py`): Async-based main orchestration with state machine for work/break cycles
2. **Platform Factory** (`move_me/platforms/factory.py`): Auto-detects Linux/Windows, imports platform-specific overlay implementations
3. **ConfigManager** (`move_me/config/manager.py`): Merges defaults from `default_config.json` with user config at `~/.config/move-me/config.json`
4. **StateManager** (`move_me/core/state.py`): JSON persistence for daily override counts, break statistics, auto-resets at midnight

### Key Patterns

-   **Factory Pattern**: `get_screen_locker()` dynamically imports `LinuxScreenLocker` or `WindowsScreenLocker`
-   **Abstract Base**: All platform implementations inherit from `ScreenLocker` in `platforms/base.py`
-   **Async State Machine**: TimerManager runs perpetual `_timer_loop()` checking break times every second
-   **Configuration Merging**: Default config + user config + CLI arguments (CLI takes precedence)
-   **GUI Overlays**: Linux uses tkinter for fullscreen break overlays with timer and override button

## Platform-Specific Implementation

### Adding New Platforms

1. Create `move_me/platforms/{platform}.py` inheriting from `ScreenLocker`
2. Implement required methods: `lock_screen()`, `unlock_screen()`, `is_screen_locked()`, `can_auto_unlock()`
3. Implement overlay methods: `show_break_overlay()`, `hide_break_overlay()`, `is_overlay_active()`
4. Add platform detection to `factory.py` (follows pattern: `platform.system().lower()`)

### Break Overlay System

-   **Linux**: Uses tkinter fullscreen overlay (`LinuxBreakOverlay`) with random motivational messages, countdown timer, and override button
-   **Windows**: Planned implementation (currently falls back to screen locking)

### Legacy Screen Locking Commands

-   **Linux**: Tries `xdg-screensaver lock`, `gnome-screensaver-command --lock`, `loginctl lock-session`, etc.
-   **Windows**: Uses `rundll32.exe user32.dll,LockWorkStation` or Windows API via `ctypes`

## Configuration System

### Config Hierarchy (highest precedence first)

1. CLI arguments (`--work`, `--break`, `--overrides`)
2. Custom config file (`--config path/to/config.yaml`)
3. User config (`~/.config/move-me/config.json`)
4. Default config (`move_me/config/default_config.json`)

### State File Location

-   Configurable via `state_file` setting (default: `move_me_state.json` in config directory)
-   Contains override counts, break statistics, automatically resets daily counters

## Development Workflows

### Running & Testing

```bash
# Development mode (short cycles for testing)
uv run move-me main --work 1 --break 1 --dry-run --verbose

# Production-like test
uv run move-me main --work 30 --break 5 --verbose

# Show current config/status
uv run move-me config --show
uv run move-me status
```

### Adding Dependencies

```bash
uv add package-name              # Runtime dependency
uv add --dev pytest black mypy   # Dev dependency
```

## Timer State Machine

### Key States & Properties

-   `_running`: Timer active flag
-   `_in_break`: Currently in break period
-   `_paused`: Timer paused (only when not in break)
-   `_next_break_time`: Scheduled break datetime
-   `_break_end_time`: When current break ends

### Countdown Notifications

Single configurable notification time (default: **30s**) before break
Uses exact second matching in `_send_countdown_notifications()` - be careful when modifying timing logic.

## Override System

-   Daily limits tracked in StateManager with automatic midnight reset
-   `can_use_override()` checks current day vs `last_run_date` in state file
-   Override usage decrements from daily limit, persists to state immediately

## Cross-Platform Considerations

### Break Overlay System

-   **Linux**: Uses tkinter for fullscreen GUI overlay with motivational messages, countdown timer, and override button
-   **Windows**: Planned implementation (currently falls back to legacy screen locking)
-   Overlay blocks user input except for the override button

### Legacy Screen Lock Detection Methods (for fallback)

-   **Linux**: Multiple fallback methods via `xdg-screensaver status`, `gnome-screensaver-command --query`, `loginctl show-session`
-   **Windows**: Uses `GetForegroundWindow()`, desktop name detection for "Winlogon" desktop
-   Returns `ScreenState.UNKNOWN` when detection fails

### Notification Fallbacks

Uses `plyer` library with console fallback if notifications unavailable.

## Common Patterns & Conventions

### Async/Await Usage

-   All timer operations use `asyncio` - TimerManager has both sync `start()` and async `start_async()`
-   Main event loop in `run_timer()` function, not in TimerManager class
-   Use `asyncio.create_task()` for concurrent break operations

### Error Handling

-   Platform operations wrapped in try/catch with logging
-   Configuration errors logged with fallback to defaults
-   Overlay failures show user notifications, don't crash app

### Logging Pattern

```python
from move_me.utils.logger import get_logger
logger = get_logger()  # Always use this pattern, not logging.getLogger()
```

## File Structure

```
move_me/
├── main.py           # Typer CLI entry point
├── config/           # ConfigManager + default_config.json
├── core/             # TimerManager, StateManager, NotificationManager
├── platforms/        # Platform abstractions + Linux/Windows implementations
└── utils/            # Logging utilities
```

## Testing & Debugging

-   Use `--dry-run` flag to test without overlay display
-   Use `--verbose` for detailed async timing logs
-   Check state file contents for override/break statistics
-   Platform detection issues debuggable via factory.py logs
