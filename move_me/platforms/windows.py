"""Windows-specific implementations for screen locking and process monitoring."""

import subprocess
import sys

from move_me.platforms.base import ScreenLocker, ScreenState
from move_me.utils.logger import get_logger

# Windows-specific imports (only available on Windows)
if sys.platform == "win32":
    try:
        import ctypes
        import ctypes.wintypes
        from ctypes import windll

        WINDOWS_APIS_AVAILABLE = True
    except ImportError:
        WINDOWS_APIS_AVAILABLE = False
        ctypes = None
        windll = None
else:
    WINDOWS_APIS_AVAILABLE = False
    ctypes = None
    windll = None


class WindowsScreenLocker(ScreenLocker):
    """Windows implementation of screen locking functionality."""

    def __init__(self):
        self.logger = get_logger()
        if not WINDOWS_APIS_AVAILABLE:
            self.logger.warning("Windows APIs not available")

    def lock_screen(self) -> bool:
        """Lock the Windows screen."""
        try:
            if not WINDOWS_APIS_AVAILABLE or windll is None:
                # Fallback to rundll32 method
                result = subprocess.run(
                    ["rundll32.exe", "user32.dll,LockWorkStation"],
                    check=False,
                    capture_output=True,
                )
                return result.returncode == 0
            else:
                # Use Windows API for better control
                success = windll.user32.LockWorkStation()
                return bool(success)
        except Exception as e:
            self.logger.error(f"Failed to lock screen: {e}")
            return False

    def unlock_screen(self) -> bool:
        """Unlock the screen (not supported on Windows)."""
        self.logger.warning("Auto-unlock not supported on Windows")
        return False

    def is_screen_locked(self) -> ScreenState:
        """Check if screen is currently locked."""
        if not WINDOWS_APIS_AVAILABLE or ctypes is None or windll is None:
            return ScreenState.UNKNOWN

        try:
            # Check if workstation is locked
            # This uses GetForegroundWindow and other APIs to determine lock state

            # Method 1: Check if the current desktop is the secure desktop
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32

            # Get current thread ID
            thread_id = kernel32.GetCurrentThreadId()

            # Get the desktop name for the current thread
            desktop_handle = user32.GetThreadDesktop(thread_id)
            if not desktop_handle:
                return ScreenState.UNKNOWN

            desktop_name = ctypes.create_unicode_buffer(256)
            name_length = 256 * 2  # 256 wide characters

            if not user32.GetUserObjectInformationW(
                desktop_handle, 2, desktop_name, name_length, None
            ):
                return ScreenState.UNKNOWN

            # If desktop name is "Winlogon", the screen is locked
            if desktop_name.value == "Winlogon":
                return ScreenState.LOCKED

            # Method 2: Check foreground window
            foreground_window = user32.GetForegroundWindow()
            if not foreground_window:
                return ScreenState.LOCKED  # No foreground window usually means locked

            # Get the class name of the foreground window
            class_name = ctypes.create_unicode_buffer(256)
            if user32.GetClassNameW(foreground_window, class_name, 256):
                # Check for known lock screen class names
                if (
                    "LockApp" in class_name.value
                    or "Windows.UI.Core" in class_name.value
                ):
                    return ScreenState.LOCKED

            return ScreenState.UNLOCKED

        except Exception as e:
            self.logger.error(f"Error checking screen lock state: {e}")
            return ScreenState.UNKNOWN

    def can_auto_unlock(self) -> bool:
        """Check if this platform supports automatic unlocking."""
        return False  # Windows doesn't support auto-unlock

    def show_break_overlay(
        self,
        messages,
        break_duration_seconds: int,
        on_override=None,
    ) -> bool:
        """Show a break overlay (not implemented for Windows yet)."""
        self.logger.warning("Break overlay not yet implemented for Windows")
        # For now, fall back to screen locking
        return self.lock_screen()

    def hide_break_overlay(self) -> bool:
        """Hide the break overlay (not implemented for Windows yet)."""
        self.logger.warning("Break overlay not yet implemented for Windows")
        return False

    def is_overlay_active(self) -> bool:
        """Check if break overlay is currently active (not implemented for Windows yet)."""
        return False
