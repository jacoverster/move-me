"""Cross-platform notification management for Move Me."""

try:
    from plyer import notification

    PLYER_AVAILABLE = True
except ImportError:
    PLYER_AVAILABLE = False

from move_me.utils.logger import get_logger


class NotificationManager:
    """Manages cross-platform notifications."""

    def __init__(self, app_name: str = "Move Me", enable_sound: bool = True):
        self.app_name = app_name
        self.enable_sound = enable_sound
        self.logger = get_logger()

        if not PLYER_AVAILABLE:
            self.logger.warning(
                "Plyer not available, notifications will fall back to console output"
            )

    def show_notification(self, title: str, message: str, timeout: int = 5) -> None:
        """Show a system notification."""
        if PLYER_AVAILABLE:
            try:
                notification.notify(
                    title=title,
                    message=message,
                    app_name=self.app_name,
                    timeout=timeout,
                )
                self.logger.debug(f"Notification shown: {title} - {message}")
                return
            except Exception as e:
                self.logger.error(f"Failed to show notification: {e}")

        # Fallback to console output
        print(f"[{self.app_name}] {title}: {message}")

    def show_countdown_warning(self, seconds_remaining: int) -> None:
        """Show countdown warning before break."""
        if seconds_remaining > 60:
            time_str = f"{seconds_remaining // 60} minute(s)"
        else:
            time_str = f"{seconds_remaining} second(s)"

        title = "Break Time Approaching"
        message = f"Screen will lock in {time_str}"

        # Use shorter timeout for more urgent warnings
        timeout = 3 if seconds_remaining <= 10 else 5

        self.show_notification(title, message, timeout=timeout)

    def show_break_starting(self, duration_minutes: int) -> None:
        """Show notification when break starts."""
        title = "Break Time!"
        message = f"Taking a {duration_minutes}-minute break. Screen is now locking."

        self.show_notification(title, message, timeout=3)

    def show_break_ending(self) -> None:
        """Show notification when break ends."""
        title = "Break Complete"
        message = "Break time is over. Welcome back!"

        self.show_notification(title, message, timeout=3)

    def show_override_used(self, remaining_overrides: int) -> None:
        """Show notification when override is used."""
        title = "Break Skipped"
        if remaining_overrides > 0:
            message = (
                f"Break skipped. {remaining_overrides} override(s) remaining today."
            )
        else:
            message = "Break skipped. No more overrides available today."

        self.show_notification(title, message, timeout=5)

    def show_error(self, error_message: str) -> None:
        """Show error notification."""
        title = "Move Me Error"
        message = error_message

        self.show_notification(title, message, timeout=10)

    def show_status(self, message: str) -> None:
        """Show status notification."""
        title = "Move Me Status"

        self.show_notification(title, message, timeout=3)
