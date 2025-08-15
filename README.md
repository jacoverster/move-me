# Move Me - Automated Break Overlay Tool

**Move Me** is a cross-platform application that helps you take regular breaks by automatically showing a fullscreen overlay at configurable intervals. It includes manual override limits to ensure you maintain healthy work habits while accommodating real-world needs.

**WARNING** This project is 99% vide-coded!

## Features

### Core Functionality
- ⏰ **Automatic break overlay** every 30 minutes (configurable)
- 🔒 **Configurable break duration** (default: 5 minutes)
- 🔔 **Countdown notification** 30 seconds before break (configurable)
- 🚫 **Manual override system** with daily limits (default: 3 per day)
- 📊 **Break statistics tracking** and state persistence

### Smart Features
- 💻 **Cross-platform support** - Linux (Ubuntu/Arch), Windows, extensible to macOS
- 🧪 **Dry-run mode** for testing without actually showing the overlay

### Configuration
- 📝 **JSON/YAML configuration files** with CLI argument overrides
- 🎛️ **Comprehensive CLI interface** with help and status commands
- 🔊 **Notification sound control**
- 📋 **Logging levels** and verbose output

## Installation

### Prerequisites
- Python 3.13 or later
- [uv](https://github.com/astral-sh/uv) package manager

### Install from Source
```bash
git clone <repository-url>
cd move-me
uv sync
```

### Linux Dependencies (Optional)
For better notification support on Linux:
```bash
# Ubuntu/Debian
sudo apt install python3-dbus

# Arch Linux
sudo pacman -S python-dbus
```

## Quick Start

### Basic Usage
```bash
# Start with default settings (30min work, 5min break)
uv run move-me main

# Custom durations
uv run move-me main --work 60 --break 10

# Test mode (no actual break overlay)
uv run move-me main --dry-run --work 1 --break 1
```

### Configuration Management
```bash
# Show current configuration
uv run move-me config --show

# Reset to defaults
uv run move-me config --reset

# Check application status
uv run move-me status
```

## Command Line Options

### Main Command
```
uv run move-me main [OPTIONS]

Options:
  --work, -w INTEGER       Work duration in minutes before break [default: 30]
  --break, -b INTEGER      Break duration in minutes [default: 5]
  --overrides, -o INTEGER  Daily limit for manual overrides [default: 3]
  --config, -c PATH        Path to custom configuration file
  --no-sound              Disable notification sounds
  --verbose, -v           Enable verbose logging
  --dry-run               Run without actually showing the overlay
  --help                  Show help message
```

### Configuration Commands
```
uv run move-me config [OPTIONS]

Options:
  --show    Show current configuration
  --reset   Reset configuration to defaults
```

### Status Command
```
uv run move-me status

Shows current application status and statistics
```

## Configuration

### Configuration File
Move Me automatically creates a configuration file at:
- **Linux**: `~/.config/move-me/config.json`
- **Windows**: `%APPDATA%/move-me/config.json`

### Default Configuration
```json
{
  "work_duration_minutes": 30,
  "break_duration_minutes": 5,
  "warning_time_seconds": 30,
  "daily_override_limit": 3,
  "notification_sound": true,
  "log_level": "INFO",
  "auto_start": false,
  "auto_lock_enabled": true,
  "state_file": "move_me_state.json",
  "overlay_messages": [
    "Time to take a break! Your eyes and body need rest.",
    "Step away from the screen. Move around, stretch, and relax.",
    "A short break now will help you stay productive longer.",
    "Remember: regular breaks prevent strain and boost creativity."
  ]
}
```

### Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `work_duration_minutes` | Minutes of work before break | 30 |
| `break_duration_minutes` | Duration of break in minutes | 5 |
| `warning_time_seconds` | When to show countdown warning | 30 |
| `daily_override_limit` | Max manual overrides per day | 3 |
| `notification_sound` | Enable notification sounds | true |
| `log_level` | Logging level (DEBUG/INFO/WARNING/ERROR) | "INFO" |
| `auto_start` | Start automatically (future feature) | false |
| `auto_lock_enabled` | Actually show the break overlay | true |
| `state_file` | Filename for state persistence | "move_me_state.json" |
| `overlay_messages` | List of motivational break messages | (see config file) |

## Platform Support

### Linux (Ubuntu/Arch)
- **Break overlay**: Fullscreen GUI overlay with timer and override button
- **Lock detection**: Multiple methods for reliable state detection (legacy)
- **Notifications**: Native Linux notifications via `plyer`

### Windows
- **Break overlay**: Fullscreen GUI overlay (planned - currently falls back to screen locking)
- **Lock detection**: Windows API calls for accurate state detection (legacy)
- **Notifications**: Native Windows notifications

### macOS (Planned)
- Extensible architecture ready for macOS implementation
- Will support native macOS overlay system and notification systems

## How It Works

### Timer Cycle
1. **Work Period**: Timer runs for configured duration (default: 30 minutes)
2. **Countdown Warning**: Notification 30 seconds before break (configurable)
3. **Break Start**: Fullscreen overlay appears, break timer begins
4. **Break Period**: Overlay shows motivational message and countdown for break duration (default: 5 minutes)
5. **Break End**: Overlay disappears automatically, new work period begins

### Smart Features
- **Manual Overrides**: End breaks early (limited per day)
- **State Persistence**: Remembers statistics and override usage across restarts
- **Graceful Shutdown**: Handles Ctrl+C and system signals properly

### Override System
- Daily limit of manual overrides (default: 3)
- Counter resets at midnight
- Prevents break avoidance while allowing flexibility
- Visual feedback shows remaining overrides

## Development

### Architecture
```
move_me/
├── config/          # Configuration management
├── core/           # Core timer and notification logic
├── platforms/      # Platform-specific implementations
├── utils/          # Logging and utilities
└── main.py         # CLI entry point
```

### Key Components
- **TimerManager**: Core timing logic and break orchestration
- **ConfigManager**: Configuration loading and validation
- **StateManager**: Persistent state and statistics tracking
- **NotificationManager**: Cross-platform notifications
- **Platform Abstractions**: Screen locking implementations
- **Factory Pattern**: Automatic platform detection

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

## Troubleshooting

### Common Issues

**Notifications not working on Linux:**
```bash
# Install dbus support
sudo apt install python3-dbus  # Ubuntu/Debian
sudo pacman -S python-dbus     # Arch Linux
```

**Overlay not appearing:**
- Check if you have GUI/X11 access
- Try running in `--dry-run` mode first
- Check logs with `--verbose` flag
- Ensure tkinter is available (`python3-tk` package on Linux)

**Permission issues:**
- Ensure you have permission to lock the screen
- Some desktop environments require additional setup

### Logs and Debugging
```bash
# Enable verbose logging
uv run move-me main --verbose

# Check configuration
uv run move-me config --show

# Test without locking
uv run move-me main --dry-run
```

### State and Configuration Locations
- **Linux**: `~/.config/move-me/`
- **Windows**: `%APPDATA%/move-me/`

## License

[Add your license here]

## Changelog

### v0.1.0 (Initial Release)
- ✅ Core timer functionality with configurable durations
- ✅ Cross-platform break overlay system (Linux implemented, Windows planned)
- ✅ Manual override system with daily limits
- ✅ Configuration management with JSON/YAML support
- ✅ Comprehensive CLI interface
- ✅ Single notification system with countdown warning
- ✅ State persistence and statistics tracking
- ✅ Dry-run mode for testing
- ✅ Graceful shutdown handling
- ✅ Customizable motivational break messages

---

**Move Me** - Take breaks with gentle reminders, stay healthy, be productive! 🚀
