"""State management for Move Me."""

import json
from datetime import datetime, date
from pathlib import Path
from typing import Dict, Any
from move_me.utils.logger import get_logger


class StateManager:
    """Manages persistent state for the application."""

    def __init__(self, state_file: Path):
        self.state_file = state_file
        self.logger = get_logger()
        self._state = self._load_state()

    def _load_state(self) -> Dict[str, Any]:
        """Load state from file."""
        if not self.state_file.exists():
            return self._create_default_state()

        try:
            with open(self.state_file, "r") as f:
                state = json.load(f)

            # Validate and migrate state if needed
            return self._validate_state(state)

        except json.JSONDecodeError as e:
            self.logger.warning(f"Invalid JSON in state file {self.state_file}: {e}")
            self.logger.info("Creating new state file")
            return self._create_default_state()
        except Exception as e:
            self.logger.warning(f"Error loading state file {self.state_file}: {e}")
            self.logger.info("Creating new state file")
            return self._create_default_state()

    def _create_default_state(self) -> Dict[str, Any]:
        """Create default state."""
        return {
            "last_run_date": None,
            "overrides_used_today": 0,
            "total_overrides": 0,
            "total_breaks_taken": 0,
            "total_breaks_skipped": 0,
            "last_break_time": None,
            "version": "0.1.0",
        }

    def _validate_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and migrate state structure."""
        default_state = self._create_default_state()

        # Ensure all required keys exist
        for key, default_value in default_state.items():
            if key not in state:
                state[key] = default_value

        # Reset daily counters if it's a new day
        today = date.today().isoformat()
        if state.get("last_run_date") != today:
            state["overrides_used_today"] = 0
            state["last_run_date"] = today
            self.logger.info("New day detected, resetting daily counters")

        return state

    def save_state(self) -> None:
        """Save current state to file."""
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)

            # Update last run date
            self._state["last_run_date"] = date.today().isoformat()

            with open(self.state_file, "w") as f:
                json.dump(self._state, f, indent=2, default=str)

            self.logger.debug(f"State saved to {self.state_file}")

        except Exception as e:
            self.logger.error(f"Error saving state: {e}")

    def can_use_override(self, daily_limit: int) -> bool:
        """Check if user can use an override today."""
        return self._state["overrides_used_today"] < daily_limit

    def use_override(self) -> bool:
        """Use one override if available."""
        if not self.can_use_override(999):  # Check without limit first
            return False

        self._state["overrides_used_today"] += 1
        self._state["total_overrides"] += 1
        self.save_state()
        self.logger.info(
            f"Override used. Total today: {self._state['overrides_used_today']}"
        )
        return True

    def record_break_taken(self) -> None:
        """Record that a break was taken."""
        self._state["total_breaks_taken"] += 1
        self._state["last_break_time"] = datetime.now().isoformat()
        self.save_state()
        self.logger.info("Break taken recorded")

    def record_break_skipped(self) -> None:
        """Record that a break was skipped (due to override)."""
        self._state["total_breaks_skipped"] += 1
        self.save_state()
        self.logger.info("Break skipped recorded")

    def get_overrides_remaining_today(self, daily_limit: int) -> int:
        """Get number of overrides remaining today."""
        return max(0, daily_limit - self._state["overrides_used_today"])

    def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics."""
        return {
            "overrides_used_today": self._state["overrides_used_today"],
            "total_overrides": self._state["total_overrides"],
            "total_breaks_taken": self._state["total_breaks_taken"],
            "total_breaks_skipped": self._state["total_breaks_skipped"],
            "last_break_time": self._state["last_break_time"],
        }
