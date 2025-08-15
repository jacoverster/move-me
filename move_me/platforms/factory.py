"""Platform detection and factory for creating platform-specific instances."""

import platform

from move_me.platforms.base import ScreenLocker
from move_me.utils.logger import get_logger

# Constants
MACOS_NOT_IMPLEMENTED_MSG = "macOS support not yet implemented"


def get_platform_name() -> str:
    """Get the current platform name."""
    return platform.system().lower()


def get_screen_locker() -> ScreenLocker:
    """Factory function to create platform-specific screen locker."""
    platform_name = get_platform_name()
    logger = get_logger()

    if platform_name == "linux":
        from move_me.platforms.linux import LinuxScreenLocker

        logger.debug("Creating Linux screen locker")
        return LinuxScreenLocker()
    elif platform_name == "windows":
        from move_me.platforms.windows import WindowsScreenLocker

        logger.debug("Creating Windows screen locker")
        return WindowsScreenLocker()
    elif platform_name == "darwin":  # macOS
        # Note: macOS support planned for future release
        logger.error(MACOS_NOT_IMPLEMENTED_MSG)
        raise NotImplementedError(MACOS_NOT_IMPLEMENTED_MSG)
    else:
        logger.error(f"Unsupported platform: {platform_name}")
        raise NotImplementedError(f"Unsupported platform: {platform_name}")


def is_supported_platform() -> bool:
    """Check if the current platform is supported."""
    platform_name = get_platform_name()
    return platform_name in ["linux", "windows"]
