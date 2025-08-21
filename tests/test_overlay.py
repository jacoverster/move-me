#!/usr/bin/env python3
"""Simple test script to show the Linux break overlay."""

import time
from move_me.core.overlay import LinuxBreakOverlay


def test_override():
    """Test override callback."""
    # This is a simple test that verifies the import works
    from move_me.core.overlay import LinuxBreakOverlay

    assert LinuxBreakOverlay is not None


def main():
    """Test the overlay display."""
    print("Starting overlay test...")

    # Create overlay with test messages
    messages = [
        "Time for a break!",
        "Step away from your screen",
        "Stretch your legs and rest your eyes",
    ]

    overlay = LinuxBreakOverlay(
        messages=messages,
        break_duration_seconds=10,  # 10 second test
        on_override=test_override,
    )

    print("Showing overlay...")
    overlay.show_overlay()

    # Wait for the overlay to be active
    time.sleep(1)

    print(
        "Overlay should now be visible. It will auto-close after 10 seconds or you can click override."
    )

    # Wait for overlay to finish
    while overlay.is_active():
        time.sleep(0.5)

    print("Overlay test completed.")


if __name__ == "__main__":
    main()
