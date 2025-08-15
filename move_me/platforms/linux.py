"""Linux-specific implementations for screen locking and process monitoring."""

import subprocess
from typing import Callable, List, Optional

from move_me.platforms.base import ScreenLocker, ScreenState
from move_me.platforms.linux_overlay import LinuxBreakOverlay
from move_me.utils.logger import get_logger


class LinuxScreenLocker(ScreenLocker):
    """Linux implementation of screen locking functionality."""

    def __init__(self):
        self.logger = get_logger()
        self._lock_command = self._detect_lock_command()
        self._unlock_command = None  # Linux typically doesn't support auto-unlock
        self._overlay: Optional[LinuxBreakOverlay] = None

    def _detect_lock_command(self) -> Optional[str]:
        """Detect the best screen lock command for this system."""
        commands = [
            "xdg-screensaver lock",  # Universal
            "gnome-screensaver-command --lock",  # GNOME
            "xscreensaver-command -lock",  # XScreensaver
            "dm-tool lock",  # LightDM
            "loginctl lock-session",  # systemd
            "i3lock",  # i3wm
            "slock",  # suckless
        ]

        for cmd in commands:
            try:
                # Test if command exists
                cmd_parts = cmd.split()
                result = subprocess.run(
                    ["which", cmd_parts[0]], capture_output=True, timeout=5
                )
                if result.returncode == 0:
                    self.logger.debug(f"Found screen lock command: {cmd}")
                    return cmd
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue

        self.logger.warning("No screen lock command found")
        return None

    def lock_screen(self) -> bool:
        """Lock the screen."""
        if not self._lock_command:
            self.logger.error("No screen lock command available")
            return False

        try:
            result = subprocess.run(
                self._lock_command.split(), capture_output=True, timeout=10
            )

            if result.returncode == 0:
                self.logger.info("Screen locked successfully")
                return True
            else:
                self.logger.error(f"Failed to lock screen: {result.stderr.decode()}")
                return False

        except subprocess.TimeoutExpired:
            self.logger.error("Screen lock command timed out")
            return False
        except Exception as e:
            self.logger.error(f"Error locking screen: {e}")
            return False

    def unlock_screen(self) -> bool:
        """Unlock the screen (not supported on Linux)."""
        self.logger.warning("Auto-unlock not supported on Linux")
        return False

    def is_screen_locked(self) -> ScreenState:
        """Check if screen is currently locked."""
        try:
            # Try multiple detection methods
            state = self._check_xdg_screensaver()
            if state != ScreenState.UNKNOWN:
                return state

            state = self._check_gnome_screensaver()
            if state != ScreenState.UNKNOWN:
                return state

            state = self._check_loginctl()
            if state != ScreenState.UNKNOWN:
                return state

            return ScreenState.UNKNOWN

        except Exception as e:
            self.logger.error(f"Error checking screen lock state: {e}")
            return ScreenState.UNKNOWN

    def _check_xdg_screensaver(self) -> ScreenState:
        """Check XDG screensaver status."""
        try:
            result = subprocess.run(
                ["xdg-screensaver", "status"], capture_output=True, timeout=5
            )
            if result.returncode == 0:
                output = result.stdout.decode().strip().lower()
                if "enabled" in output or "active" in output:
                    return ScreenState.LOCKED
                elif "disabled" in output:
                    return ScreenState.UNLOCKED
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        return ScreenState.UNKNOWN

    def _check_gnome_screensaver(self) -> ScreenState:
        """Check GNOME screensaver status."""
        try:
            result = subprocess.run(
                ["gnome-screensaver-command", "--query"], capture_output=True, timeout=5
            )
            if result.returncode == 0:
                output = result.stdout.decode().strip().lower()
                if "active" in output:
                    return ScreenState.LOCKED
                elif "inactive" in output:
                    return ScreenState.UNLOCKED
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        return ScreenState.UNKNOWN

    def _check_loginctl(self) -> ScreenState:
        """Check loginctl session status."""
        try:
            result = subprocess.run(
                ["loginctl", "show-session", "-p", "LockedHint"],
                capture_output=True,
                timeout=5,
            )
            if result.returncode == 0:
                output = result.stdout.decode().strip()
                if "LockedHint=yes" in output:
                    return ScreenState.LOCKED
                elif "LockedHint=no" in output:
                    return ScreenState.UNLOCKED
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        return ScreenState.UNKNOWN

    def can_auto_unlock(self) -> bool:
        """Check if this platform supports automatic unlocking."""
        return False  # Linux doesn't typically support auto-unlock

    def show_break_overlay(
        self,
        messages: List[str],
        break_duration_seconds: int,
        on_override: Optional[Callable] = None,
    ) -> bool:
        """Show a break overlay instead of locking screen."""
        try:
            if self._overlay and self._overlay.is_active():
                self.logger.warning("Overlay already active")
                return False

            self._overlay = LinuxBreakOverlay(
                messages=messages,
                break_duration_seconds=break_duration_seconds,
                on_override=on_override,
            )

            self._overlay.show_overlay()
            self.logger.info("Break overlay displayed successfully")
            return True

        except Exception as e:
            self.logger.error(f"Error showing break overlay: {e}")
            return False

    def hide_break_overlay(self) -> bool:
        """Hide the break overlay."""
        try:
            if self._overlay:
                self._overlay.hide_overlay()
                self._overlay = None
                self.logger.info("Break overlay hidden successfully")
                return True
            else:
                self.logger.warning("No overlay to hide")
                return False

        except Exception as e:
            self.logger.error(f"Error hiding break overlay: {e}")
            return False

    def is_overlay_active(self) -> bool:
        """Check if break overlay is currently active."""
        return self._overlay is not None and self._overlay.is_active()
