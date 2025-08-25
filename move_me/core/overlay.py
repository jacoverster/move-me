"""Linux GUI overlay for break enforcement.

Font Rendering Improvements:
- Uses Noto Sans and Liberation fonts as primary choices (excellent Linux rendering)
- Falls back through high-quality font families: DejaVu Sans, Ubuntu, Arial
- Monospace fonts prioritize Noto Sans Mono and Liberation Mono for timer
- Creates Font objects for better rendering control
- Removes borders and highlights that can cause pixelation
- Uses proper font weights (bold for headers, normal for body text)
- Optimized font sizes for clarity and readability

Color and Design Improvements:
- Parameterized color scheme for easy customization
- High contrast colors for better readability
- Clean, modern flat design with no borders
- Consistent color usage throughout interface
"""

import random
import os
import tkinter as tk
import tkinter.font as tkfont
from datetime import datetime
from typing import Callable, List, Literal, Optional, Tuple

from move_me.utils.logger import get_logger


class OverlayConfig:
    """Configuration class for overlay appearance."""

    FONT_FAMILIES = {
        "primary": ["Noto Sans", "Liberation Sans", "DejaVu Sans", "Ubuntu", "Arial"],
        "monospace": [
            "Noto Sans Mono",
            "Liberation Mono",
            "DejaVu Sans Mono",
            "Ubuntu Mono",
            "Consolas",
            "Monaco",
        ],
        "fallback": ["TkDefaultFont"],  # System fallback
    }

    FONT_SIZES = {
        "title": 32,  # Main message
        "timer": 56,  # Timer display
        "button": 16,  # Button text
        "warning": 12,  # Warning text
    }

    COLORS = {
        "background": "#2c3e50",  # Dark blue-gray
        "text_primary": "#ecf0f1",  # Light gray-white
        "text_secondary": "#bdc3c7",  # Medium gray
        "timer_active": "#e74c3c",  # Red for countdown
        "timer_complete": "#27ae60",  # Green when done
        "button_bg": "#e67e22",  # Orange button
        "button_hover": "#d35400",  # Darker orange on hover
        "button_text": "#ffffff",  # White button text
    }

    @staticmethod
    def get_best_font(
        font_type: str, size: int, weight: Literal["normal", "bold"] = "normal"
    ) -> Tuple[str, int, str]:
        """Get the best available font for the given type."""

        families = OverlayConfig.FONT_FAMILIES.get(
            font_type, OverlayConfig.FONT_FAMILIES["primary"]
        )

        for family in families:
            try:
                # Create a test font to verify it exists
                test_font = tkfont.Font(family=family, size=size, weight=weight)
                if test_font.actual("family").lower() == family.lower():
                    return (family, size, weight)
            except (tk.TclError, Exception):
                continue

        # Final fallback
        return (families[-1], size, weight)


class LinuxBreakOverlay:
    """GUI overlay that prevents user interaction during breaks."""

    def __init__(
        self,
        messages: List[str],
        break_duration_seconds: int,
        on_override: Optional[Callable] = None,
        config: Optional[OverlayConfig] = None,
    ):
        self.messages = messages
        self.break_duration_seconds = break_duration_seconds
        self.on_override = on_override
        self.config = config or OverlayConfig()
        self.logger = get_logger()

        self.is_showing = False
        self.start_time: Optional[datetime] = None

        # UI elements
        self.message_label: Optional[tk.Label] = None
        self.timer_label: Optional[tk.Label] = None
        self.override_button: Optional[tk.Button] = None

    def show_overlay(self):
        """Show the break overlay using a Tk root in the calling thread.

        This method blocks until the overlay is closed. If no graphical
        display is detected (commonly in headless CI), the method logs and
        returns without raising exceptions.
        """

        if self.is_showing:
            return

        # Avoid Tcl/Tk errors in headless environments by checking common
        # display environment variables used by X11 and Wayland.
        if not any(key in os.environ for key in ("DISPLAY", "WAYLAND_DISPLAY", "XDG_RUNTIME_DIR")):
            self.logger.error("No graphical display detected; cannot show overlay")
            return

        # Mark as showing and record start time
        self.is_showing = True
        self.start_time = datetime.now()

        # Run overlay in the current thread. Tkinter is not thread-safe so the
        # Tk root must be created and run in the main/calling thread.
        self._should_quit = False
        self._run_overlay()

    def _run_overlay(self):
        """Run the overlay in a separate thread with its own Tk instance."""
        try:
            root = tk.Tk()
            root.title("Move Me - Break Time")
            root.configure(bg=self.config.COLORS["background"])

            # Get screen dimensions
            root.update_idletasks()  # Ensure window is ready
            screen_width = root.winfo_screenwidth()
            screen_height = root.winfo_screenheight()

            # Make window large enough to cover multiple monitors
            # Use a very large size that should cover most multi-monitor setups
            extended_width = screen_width * 3  # Cover up to 3 monitors horizontally
            extended_height = screen_height * 2  # Cover up to 2 monitors vertically

            # Position at 0,0 to start from top-left corner
            root.geometry(f"{extended_width}x{extended_height}+0+0")

            # Make window fullscreen and topmost
            root.attributes("-fullscreen", True)
            root.attributes("-topmost", True)

            # Try Linux-specific attributes
            try:
                root.attributes("-type", "splash")
            except tk.TclError:
                pass

            root.overrideredirect(True)

            # Focus and raise the window
            root.focus_force()
            root.lift()
            root.tkraise()

            # Protocol for window close (prevent closing)
            root.protocol("WM_DELETE_WINDOW", self._on_closing)

            # Capture all input events
            root.bind("<Key>", self._block_input)
            root.bind("<Button>", self._block_input)
            root.bind("<Motion>", self._block_input)
            root.bind("<ButtonPress>", self._block_input)
            root.bind("<ButtonRelease>", self._block_input)
            root.bind("<KeyPress>", self._block_input)
            root.bind("<KeyRelease>", self._block_input)

            # Grab keyboard and mouse input
            root.grab_set_global()
            root.focus_set()

            # Store root reference
            self._thread_root = root

            # Populate the overlay
            self._populate_overlay_in_thread(root)

            # Start periodic check for quit signal using after()
            def check_quit():
                if self._should_quit:
                    try:
                        root.quit()
                    except Exception:
                        pass
                else:
                    root.after(100, check_quit)  # Check every 100ms

            root.after(100, check_quit)

            # Start the mainloop (blocks until window is destroyed or quit())
            root.mainloop()

        except Exception as e:
            self.logger.error(f"Error in overlay thread: {e}")
        finally:
            self.is_showing = False
            if hasattr(self, "_thread_root"):
                try:
                    self._thread_root.destroy()
                except Exception:
                    pass
                delattr(self, "_thread_root")

    def _populate_overlay_in_thread(self, root):
        """Populate the overlay with content (runs in overlay thread)."""
        # Center frame for content
        center_frame = tk.Frame(root, bg=self.config.COLORS["background"])
        center_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Create optimized fonts using the configuration
        title_font = self.config.get_best_font(
            "primary", self.config.FONT_SIZES["title"], "bold"
        )
        timer_font = self.config.get_best_font(
            "monospace", self.config.FONT_SIZES["timer"], "bold"
        )
        button_font = self.config.get_best_font(
            "primary", self.config.FONT_SIZES["button"], "normal"
        )
        warning_font = self.config.get_best_font(
            "primary", self.config.FONT_SIZES["warning"], "normal"
        )

        # Create Font objects - cast weight to str to avoid type issues
        self.title_font_obj = tkfont.Font(
            family=title_font[0],
            size=title_font[1],
            weight=str(title_font[2]),  # type: ignore
        )
        self.timer_font_obj = tkfont.Font(
            family=timer_font[0],
            size=timer_font[1],
            weight=str(timer_font[2]),  # type: ignore
        )
        self.button_font_obj = tkfont.Font(
            family=button_font[0],
            size=button_font[1],
            weight=str(button_font[2]),  # type: ignore
        )
        self.warning_font_obj = tkfont.Font(
            family=warning_font[0],
            size=warning_font[1],
            weight=str(warning_font[2]),  # type: ignore
        )

        # Random message with improved styling
        message = random.choice(self.messages)
        self.message_label = tk.Label(
            center_frame,
            text=message,
            font=self.title_font_obj,
            fg=self.config.COLORS["text_primary"],
            bg=self.config.COLORS["background"],
            wraplength=900,
            justify="center",
            bd=0,
            highlightthickness=0,
        )
        self.message_label.pack(pady=30)

        # Timer display with improved styling
        self.timer_label = tk.Label(
            center_frame,
            text=self._format_time_remaining(),
            font=self.timer_font_obj,
            fg=self.config.COLORS["timer_active"],
            bg=self.config.COLORS["background"],
            bd=0,
            highlightthickness=0,
        )
        self.timer_label.pack(pady=20)

        # Override button with modern styling
        self.override_button = tk.Button(
            center_frame,
            text="Override Break (Use Sparingly)",
            font=self.button_font_obj,
            bg=self.config.COLORS["button_bg"],
            fg=self.config.COLORS["button_text"],
            activebackground=self.config.COLORS["button_hover"],
            activeforeground=self.config.COLORS["button_text"],
            padx=30,
            pady=15,
            command=self._handle_override_in_thread,
            cursor="hand2",
            relief="flat",
            borderwidth=0,
            bd=0,
            highlightthickness=0,
        )
        self.override_button.pack(pady=40)

        # Warning text with improved styling
        warning_label = tk.Label(
            center_frame,
            text="This overlay will prevent interaction with your system until the break is complete.\n"
            "Use the override button only when absolutely necessary.",
            font=self.warning_font_obj,
            fg=self.config.COLORS["text_secondary"],
            bg=self.config.COLORS["background"],
            justify="center",
            wraplength=800,
            bd=0,
            highlightthickness=0,
        )
        warning_label.pack(pady=10)

        # Start timer updates
        self._update_timer_in_thread()

    def _handle_override_in_thread(self):
        """Handle override button click (runs in overlay thread)."""
        override_successful = False

        if self.on_override:
            # Call the override callback and check if it was successful
            result = self.on_override()
            override_successful = result if result is not None else False

        # Only hide the overlay if the override was successful
        if override_successful:
            # Request the overlay to quit gracefully
            # Note: is_showing will be set to False in the finally block of _run_overlay
            self._should_quit = True
        else:
            # Override failed - keep overlay active
            self.logger.info("Override was not successful, keeping overlay active")

    def _update_timer_in_thread(self):
        """Update the timer display (runs in overlay thread)."""
        if not self.is_showing or not self.timer_label:
            return

        time_remaining = self._get_time_remaining()

        if time_remaining <= 0:
            # Break time is over - automatically close overlay
            self.timer_label.config(text="00:00")
            self.timer_label.config(fg=self.config.COLORS["timer_complete"])

            # Update message to indicate break is complete
            if self.message_label:
                self.message_label.config(
                    text="Break time complete! Closing overlay..."
                )

            # Auto-close the overlay after showing completion message briefly
            if hasattr(self, "_thread_root") and self._thread_root:
                # Show completion message for 2 seconds, then auto-close
                def auto_close():
                    self._should_quit = True

                self._thread_root.after(1000, auto_close)  # Auto-close after 1 second
            return

        # Update timer display
        self.timer_label.config(text=self._format_time_remaining())

        # Schedule next update
        if hasattr(self, "_thread_root") and self._thread_root:
            self._thread_root.after(1000, self._update_timer_in_thread)

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

    def hide_overlay(self):
        """Hide the break overlay."""
        if not self.is_showing:
            return

        self.is_showing = False
        # Request the overlay to quit gracefully. The after()-driven check
        # in the mainloop will call root.quit() which ends the mainloop.
        try:
            self._should_quit = True
        except AttributeError:
            # _should_quit might not exist if overlay was never shown
            self.logger.debug("_should_quit attribute not found during hide_overlay")
        except Exception as e:
            self.logger.error(f"Error setting _should_quit flag: {e}")

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
