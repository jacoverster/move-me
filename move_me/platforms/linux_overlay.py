"""Linux GUI overlay for break enforcement."""

import random
import threading
import tkinter as tk
from datetime import datetime
from typing import Callable, List, Optional

from move_me.utils.logger import get_logger


class LinuxBreakOverlay:
    """GUI overlay that prevents user interaction during breaks."""

    def __init__(
        self,
        messages: List[str],
        break_duration_seconds: int,
        on_override: Optional[Callable] = None,
    ):
        self.messages = messages
        self.break_duration_seconds = break_duration_seconds
        self.on_override = on_override
        self.logger = get_logger()

        self.root: Optional[tk.Tk] = None
        self.overlay_thread: Optional[threading.Thread] = None
        self.is_showing = False
        self.start_time: Optional[datetime] = None

        # UI elements
        self.message_label: Optional[tk.Label] = None
        self.timer_label: Optional[tk.Label] = None
        self.override_button: Optional[tk.Button] = None

    def show_overlay(self):
        """Show the break overlay."""
        if self.is_showing:
            return

        self.is_showing = True
        self.start_time = datetime.now()

        # Run overlay in separate thread to avoid blocking
        self.overlay_thread = threading.Thread(target=self._create_overlay)
        self.overlay_thread.daemon = True
        self.overlay_thread.start()

    def hide_overlay(self):
        """Hide the break overlay."""
        if not self.is_showing:
            return

        self.is_showing = False

        if self.root:
            # Schedule the cleanup to happen in the GUI thread
            try:
                self.root.after(0, self._cleanup_overlay)
            except tk.TclError:
                # If that fails, try direct cleanup
                self._cleanup_overlay()

    def _cleanup_overlay(self):
        """Clean up the overlay window."""
        if self.root:
            try:
                self.root.quit()  # Exit the mainloop
                self.root.destroy()  # Destroy the window
            except tk.TclError:
                pass  # Window might already be destroyed
            finally:
                self.root = None

    def _create_overlay(self):
        """Create and run the overlay GUI."""
        try:
            self.root = tk.Tk()
            self.root.title("Move Me - Break Time")

            # Get screen dimensions
            self.root.update_idletasks()  # Ensure window is ready
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()

            # Make window large enough to cover multiple monitors
            # Use a very large size that should cover most multi-monitor setups
            extended_width = screen_width * 3  # Cover up to 3 monitors horizontally
            extended_height = screen_height * 2  # Cover up to 2 monitors vertically

            # Position at 0,0 to start from top-left corner
            self.root.geometry(f"{extended_width}x{extended_height}+0+0")
            self.root.configure(bg="#2c3e50")  # Dark blue-gray background

            # Make window fullscreen and topmost
            self.root.attributes("-fullscreen", True)
            self.root.attributes("-topmost", True)

            # Try Linux-specific attributes to prevent window manager interference
            try:
                self.root.attributes("-type", "splash")
            except tk.TclError:
                pass  # Not all window managers support this

            # Disable window manager decorations
            self.root.overrideredirect(True)

            # Focus and raise the window
            self.root.focus_force()
            self.root.lift()
            self.root.tkraise()

            # Center frame for content
            center_frame = tk.Frame(self.root, bg="#2c3e50")
            center_frame.place(relx=0.5, rely=0.5, anchor="center")

            # Random message
            message = random.choice(self.messages)
            self.message_label = tk.Label(
                center_frame,
                text=message,
                font=("Arial", 24, "bold"),
                fg="white",
                bg="#2c3e50",
                wraplength=800,
                justify="center",
            )
            self.message_label.pack(pady=30)

            # Timer display
            self.timer_label = tk.Label(
                center_frame,
                text=self._format_time_remaining(),
                font=("Arial", 48, "bold"),
                fg="#e74c3c",  # Red color
                bg="#2c3e50",
            )
            self.timer_label.pack(pady=20)

            # Override button
            self.override_button = tk.Button(
                center_frame,
                text="Override Break (Use Sparingly)",
                font=("Arial", 16),
                bg="#e67e22",  # Orange
                fg="white",
                activebackground="#d35400",
                activeforeground="white",
                padx=30,
                pady=15,
                command=self._handle_override,
                cursor="hand2",
            )
            self.override_button.pack(pady=40)

            # Warning text
            warning_label = tk.Label(
                center_frame,
                text="This overlay will prevent interaction with your system until the break is complete.\n"
                "Use the override button only when absolutely necessary.",
                font=("Arial", 12),
                fg="#95a5a6",  # Light gray
                bg="#2c3e50",
                justify="center",
            )
            warning_label.pack(pady=10)

            # Update timer every second
            self._update_timer()

            # Capture all key events and mouse events more aggressively
            self.root.bind("<Key>", self._block_input)
            self.root.bind("<Button>", self._block_input)
            self.root.bind("<Motion>", self._block_input)
            self.root.bind("<ButtonPress>", self._block_input)
            self.root.bind("<ButtonRelease>", self._block_input)
            self.root.bind("<KeyPress>", self._block_input)
            self.root.bind("<KeyRelease>", self._block_input)

            # Grab keyboard and mouse input
            self.root.grab_set_global()
            self.root.focus_set()

            # Try to grab the pointer and keyboard (Linux-specific)
            try:
                # This helps ensure the window captures all input
                self.root.update()
                if self.root:
                    self.root.after(100, lambda: self.root and self.root.focus_force())
            except Exception as e:
                self.logger.warning(f"Could not grab input focus: {e}")

            # Protocol for window close (prevent closing)
            self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

            # Start the GUI event loop
            self.root.mainloop()

        except Exception as e:
            self.logger.error(f"Error creating overlay: {e}")
        finally:
            self.is_showing = False

    def _update_timer(self):
        """Update the timer display."""
        if not self.is_showing or not self.root or not self.timer_label:
            return

        time_remaining = self._get_time_remaining()

        if time_remaining <= 0:
            # Break time is over - close overlay naturally
            self.is_showing = False
            if self.root:
                self.root.quit()
                self.root.destroy()
                self.root = None
            return

        # Update timer display
        self.timer_label.config(text=self._format_time_remaining())

        # Schedule next update
        self.root.after(1000, self._update_timer)

    def _get_time_remaining(self) -> int:
        """Get remaining time in seconds."""
        if not self.start_time:
            return 0

        elapsed = datetime.now() - self.start_time
        remaining = self.break_duration_seconds - elapsed.total_seconds()
        return max(0, int(remaining))

    def _format_time_remaining(self) -> str:
        """Format remaining time for display."""
        seconds = self._get_time_remaining()
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"

    def _handle_override(self):
        """Handle override button click."""
        override_successful = False

        if self.on_override:
            # Call the override callback and check if it was successful
            # The callback should return True if override was used, False otherwise
            result = self.on_override()
            override_successful = result if result is not None else False

        # Only close the overlay if the override was successful
        if override_successful:
            # Set flag to stop showing and exit the mainloop
            self.is_showing = False

            if self.root:
                self.root.quit()  # Exit the mainloop
                self.root.destroy()  # Destroy the window
                self.root = None
        else:
            # Override failed - keep overlay active and optionally show feedback
            self.logger.info("Override was not successful, keeping overlay active")

    def _block_input(self, event):
        """Block keyboard and mouse input."""
        # Prevent all input except our override button
        return "break"

    def _on_closing(self):
        """Handle window close event."""
        # Don't allow closing the window
        pass

    def is_active(self) -> bool:
        """Check if overlay is currently active."""
        return self.is_showing
