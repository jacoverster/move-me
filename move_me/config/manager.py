"""Configuration management for Move Me."""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional
import yaml


class ConfigManager:
    """Manages configuration loading and validation."""

    def __init__(self):
        self.config_dir = Path.home() / ".config" / "move-me"
        self.config_file = self.config_dir / "config.json"
        self.default_config = self._load_default_config()

    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration from package."""
        default_path = Path(__file__).parent / "default_config.json"
        try:
            with open(default_path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            # Fallback if default config not found
            return {
                "work_duration_minutes": 45,
                "break_duration_minutes": 5,
                "warning_time_seconds": 30,
                "daily_override_limit": 3,
                "notification_sound": True,
                "log_level": "INFO",
                "auto_start": False,
                "state_file": "move_me_state.json",
                "overlay_messages": [
                    "Time to take a break! Your eyes and body need rest.",
                    "Step away from the screen. Move around, stretch, and relax.",
                    "A short break now will help you stay productive longer.",
                    "Remember: regular breaks prevent strain and boost creativity.",
                    "Stand up, walk around, and give your mind a moment to refresh.",
                    "Your health is more important than any deadline.",
                    "Taking breaks is not lazy - it's essential for your wellbeing.",
                    "Look at something far away, blink often, and breathe deeply.",
                ],
            }

    def load_config(self, config_path: Optional[Path] = None) -> Dict[str, Any]:
        """Load configuration from file or create default."""
        config = self.default_config.copy()

        # Load from specified path or default location
        load_path = config_path or self.config_file

        if load_path.exists():
            try:
                with open(load_path, "r") as f:
                    if load_path.suffix.lower() in [".yml", ".yaml"]:
                        user_config = yaml.safe_load(f)
                    else:
                        user_config = json.load(f)

                # Merge user config with defaults
                config.update(user_config)
            except (json.JSONDecodeError, yaml.YAMLError, Exception) as e:
                print(f"Warning: Error loading config from {load_path}: {e}")
                print("Using default configuration.")
        else:
            # Create default config file
            self.save_config(config, load_path)

        return config

    def save_config(
        self, config: Dict[str, Any], config_path: Optional[Path] = None
    ) -> None:
        """Save configuration to file."""
        save_path = config_path or self.config_file
        save_path.parent.mkdir(parents=True, exist_ok=True)

        with open(save_path, "w") as f:
            json.dump(config, f, indent=2)

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate configuration values."""
        required_keys = [
            "work_duration_minutes",
            "break_duration_minutes",
            "warning_time_seconds",
            "daily_override_limit",
        ]

        for key in required_keys:
            if key not in config:
                print(f"Error: Missing required configuration key: {key}")
                return False

        # Validate types and ranges
        if (
            not isinstance(config["work_duration_minutes"], (int, float))
            or config["work_duration_minutes"] <= 0
        ):
            print("Error: work_duration_minutes must be a positive number")
            return False

        if (
            not isinstance(config["break_duration_minutes"], (int, float))
            or config["break_duration_minutes"] <= 0
        ):
            print("Error: break_duration_minutes must be a positive number")
            return False

        if (
            not isinstance(config["warning_time_seconds"], (int, float))
            or config["warning_time_seconds"] <= 0
        ):
            print("Error: warning_time_seconds must be a positive number")
            return False

        if (
            not isinstance(config["daily_override_limit"], int)
            or config["daily_override_limit"] < 0
        ):
            print("Error: daily_override_limit must be a non-negative integer")
            return False

        return True

    def get_state_file_path(self, config: Dict[str, Any]) -> Path:
        """Get the full path for the state file."""
        state_filename = config.get("state_file", "move_me_state.json")
        if os.path.isabs(state_filename):
            return Path(state_filename)
        else:
            return self.config_dir / state_filename
