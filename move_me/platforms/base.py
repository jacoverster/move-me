"""Abstract base classes for platform-specific implementations."""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Callable, List, Optional


class ScreenState(Enum):
    """Screen state enumeration."""

    UNLOCKED = "unlocked"
    LOCKED = "locked"
    UNKNOWN = "unknown"


class ScreenLocker(ABC):
    """Abstract base class for screen locking functionality."""

    @abstractmethod
    def lock_screen(self) -> bool:
        """Lock the screen. Returns True if successful."""
        pass

    @abstractmethod
    def unlock_screen(self) -> bool:
        """Unlock the screen. Returns True if successful."""
        pass

    @abstractmethod
    def is_screen_locked(self) -> ScreenState:
        """Check if screen is currently locked."""
        pass

    @abstractmethod
    def can_auto_unlock(self) -> bool:
        """Check if this platform supports automatic unlocking."""
        pass

    @abstractmethod
    def show_break_overlay(
        self,
        messages: List[str],
        break_duration_seconds: int,
        on_override: Optional[Callable] = None,
    ) -> bool:
        """Show a break overlay instead of locking screen. Returns True if successful."""
        pass

    @abstractmethod
    def hide_break_overlay(self) -> bool:
        """Hide the break overlay. Returns True if successful."""
        pass

    @abstractmethod
    def is_overlay_active(self) -> bool:
        """Check if break overlay is currently active."""
        pass
