"""Core timer functionality for managing screen lock cycles."""

import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Callable, Dict, Any

from move_me.core.notifications import NotificationManager
from move_me.core.state import StateManager
from move_me.platforms.factory import get_screen_locker
from move_me.utils.logger import get_logger


class TimerManager:
    """Manages the screen locking timer and break cycles."""

    def __init__(self, config: Dict[str, Any], state_file_path: Path):
        self.config = config
        self.state_manager = StateManager(state_file_path)
        self.notification_manager = NotificationManager(
            enable_sound=config.get("notification_sound", True)
        )
        self.screen_locker = get_screen_locker()
        self.logger = get_logger()

        # Timer state
        self._running = False
        self._paused = False
        self._current_task: Optional[asyncio.Task] = None
        self._next_break_time: Optional[datetime] = None
        self._break_end_time: Optional[datetime] = None
        self._in_break = False

        # Callbacks
        self._on_break_start: Optional[Callable] = None
        self._on_break_end: Optional[Callable] = None
        self._on_override_used: Optional[Callable] = None

    def set_callbacks(
        self,
        on_break_start: Optional[Callable] = None,
        on_break_end: Optional[Callable] = None,
        on_override_used: Optional[Callable] = None,
    ):
        """Set callback functions for timer events."""
        self._on_break_start = on_break_start
        self._on_break_end = on_break_end
        self._on_override_used = on_override_used

    @property
    def is_running(self) -> bool:
        """Check if timer is currently running."""
        return self._running

    @property
    def is_paused(self) -> bool:
        """Check if timer is currently paused."""
        return self._paused

    @property
    def is_in_break(self) -> bool:
        """Check if currently in a break."""
        return self._in_break

    @property
    def next_break_time(self) -> Optional[datetime]:
        """Get the time of the next scheduled break."""
        return self._next_break_time

    @property
    def break_end_time(self) -> Optional[datetime]:
        """Get the time when current break will end."""
        return self._break_end_time

    @property
    def time_until_next_break(self) -> Optional[timedelta]:
        """Get time remaining until next break."""
        if not self._next_break_time:
            return None
        return max(timedelta(0), self._next_break_time - datetime.now())

    @property
    def time_remaining_in_break(self) -> Optional[timedelta]:
        """Get time remaining in current break."""
        if not self._break_end_time or not self._in_break:
            return None
        return max(timedelta(0), self._break_end_time - datetime.now())

    def start(self):
        """Start the timer (must be called from an async context)."""
        if self._running:
            self.logger.warning("Timer already running")
            return

        self.logger.info("Starting MoveMe timer")
        self._running = True
        self._paused = False
        self._schedule_next_break()

    async def start_async(self):
        """Start the timer with async task creation."""
        self.start()
        # Start the main timer loop
        self._current_task = asyncio.create_task(self._timer_loop())
        # Give the task a moment to start
        await asyncio.sleep(0.1)

    def stop(self):
        """Stop the timer."""
        if not self._running:
            return

        self.logger.info("Stopping MoveMe timer")
        self._running = False

        if self._current_task:
            self._current_task.cancel()
            self._current_task = None

        # If in break, end it
        if self._in_break:
            self._end_break()

    def pause(self):
        """Pause the timer (only when not in break)."""
        if self._in_break:
            self.logger.warning("Cannot pause during break")
            return False

        if not self._running:
            self.logger.warning("Timer not running")
            return False

        self.logger.info("Pausing timer")
        self._paused = True
        return True

    def resume(self):
        """Resume the timer."""
        if not self._running:
            self.logger.warning("Timer not running")
            return False

        if not self._paused:
            self.logger.warning("Timer not paused")
            return False

        self.logger.info("Resuming timer")
        self._paused = False
        return True

    def force_break(self) -> bool:
        """Force an immediate break."""
        if self._in_break:
            self.logger.warning("Already in break")
            return False

        self.logger.info("Forcing immediate break")
        # Store the task to prevent garbage collection
        self._break_task = asyncio.create_task(self._start_break())
        return True

    def end_break_early(self) -> bool:
        """End the current break early (uses an override)."""
        if not self._in_break:
            self.logger.warning("Not currently in break")
            return False

        daily_limit = self.config.get("daily_override_limit", 3)

        # Check if user has overrides available
        if not self.state_manager.can_use_override(daily_limit):
            self.notification_manager.show_error(
                f"No overrides remaining. You have used all {daily_limit} overrides today"
            )
            return False

        # Use an override
        self.state_manager.use_override()
        self.logger.info("Using override to end break early")

        if self._on_override_used:
            self._on_override_used()

        self._end_break()
        return True

    def _schedule_next_break(self):
        """Schedule the next break."""
        work_duration = self.config.get("work_duration_minutes", 45)
        self._next_break_time = datetime.now() + timedelta(minutes=work_duration)
        self.logger.info(
            f"Next break scheduled for {self._next_break_time.strftime('%H:%M:%S')}"
        )

    async def _timer_loop(self):
        """Main timer loop."""
        try:
            while self._running:
                await asyncio.sleep(1)  # Check every second

                if self._paused:
                    continue

                # Check if we need to start a break
                if not self._in_break and self._next_break_time:
                    if datetime.now() >= self._next_break_time:
                        await self._start_break()

                # Check if break should end
                if self._in_break and self._break_end_time:
                    if datetime.now() >= self._break_end_time:
                        self._end_break()

                # Send countdown notifications
                self._send_countdown_notifications()

        except asyncio.CancelledError:
            self.logger.info("Timer loop cancelled")
            raise
        except Exception as e:
            self.logger.error(f"Error in timer loop: {e}")

    async def _start_break(self):
        """Start a break."""
        self.logger.info("Starting break")
        self._in_break = True

        break_duration = self.config.get("break_duration_minutes", 5)
        self._break_end_time = datetime.now() + timedelta(minutes=break_duration)

        # Show break notification
        self.notification_manager.show_break_starting(break_duration)

        if self._on_break_start:
            self._on_break_start()

        # Wait a moment for user to see notification
        await asyncio.sleep(2)

        # Show break overlay
        if self.config.get("auto_lock_enabled", True):
            try:
                # Get overlay messages from config
                overlay_messages = self.config.get(
                    "overlay_messages",
                    [
                        "Time to take a break! Your eyes and body need rest.",
                        "Step away from the screen and stretch for a moment.",
                    ],
                )

                # Calculate break duration in seconds
                break_duration_seconds = break_duration * 60

                # Show overlay with override callback
                success = self.screen_locker.show_break_overlay(
                    messages=overlay_messages,
                    break_duration_seconds=break_duration_seconds,
                    on_override=self._handle_override,
                )

                if not success:
                    self.logger.warning("Failed to show break overlay")
                    self.notification_manager.show_error(
                        "Could not show break overlay. Please take a manual break."
                    )
            except Exception as e:
                self.logger.error(f"Error showing break overlay: {e}")
                self.notification_manager.show_error(f"Break overlay error: {e}")

        # Update statistics
        self.state_manager.record_break_taken()

    def _end_break(self):
        """End the current break."""
        if not self._in_break:
            return

        self.logger.info("Ending break")
        self._in_break = False
        self._break_end_time = None

        # Hide the overlay if it's active
        try:
            if self.screen_locker.is_overlay_active():
                self.screen_locker.hide_break_overlay()
        except Exception as e:
            self.logger.error(f"Error hiding overlay at break end: {e}")

        # Schedule next break
        self._schedule_next_break()

        # Show end notification
        daily_limit = self.config.get("daily_override_limit", 3)
        remaining_overrides = self.state_manager.get_overrides_remaining_today(
            daily_limit
        )

        self.notification_manager.show_break_ending()
        if remaining_overrides > 0:
            self.notification_manager.show_status(
                f"{remaining_overrides} overrides remaining today"
            )

        if self._on_break_end:
            self._on_break_end()

    def _send_countdown_notifications(self):
        """Send countdown notifications before breaks."""
        if self._in_break or self._paused or not self._next_break_time:
            return

        time_until_break = self.time_until_next_break
        if not time_until_break:
            return

        # Get warning time from config (default to 30 seconds if not set)
        warning_time = self.config.get("warning_time_seconds", 30)
        total_seconds = int(time_until_break.total_seconds())

        # Send notification at the configured warning time
        if total_seconds == warning_time:
            self.notification_manager.show_countdown_warning(warning_time)

    def _handle_override(self):
        """Handle override button click from the break overlay."""
        daily_limit = self.config.get("daily_override_limit", 3)
        remaining_overrides = self.state_manager.get_overrides_remaining_today(
            daily_limit
        )

        if remaining_overrides > 0:
            success = self.state_manager.use_override()
            if success:
                self.logger.info("Break override used")

                if self._on_override_used:
                    self._on_override_used()

                # Hide overlay and end break
                try:
                    self.screen_locker.hide_break_overlay()
                except Exception as e:
                    self.logger.error(f"Error hiding overlay after override: {e}")

                self._end_break()

                self.notification_manager.show_override_used(remaining_overrides - 1)
                return True  # Override was successful
            else:
                self.logger.error("Failed to use override")
                return False  # Override failed
        else:
            self.logger.warning("Override attempted but daily limit reached")
            self.notification_manager.show_error(
                "Daily override limit reached. Please complete the break."
            )
            return False  # Override not allowed
