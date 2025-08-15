"""Main entry point for Move Me application."""

import asyncio
import signal
import sys
from pathlib import Path
from typing import Optional

import typer
from typing_extensions import Annotated

from move_me.config.manager import ConfigManager
from move_me.core.timer import TimerManager
from move_me.utils.logger import setup_logging, get_logger


app = typer.Typer(help="Move Me - Automated screen locking tool for regular breaks")


def signal_handler(signum: int, frame) -> None:
    """Handle shutdown signals gracefully."""
    logger = get_logger()
    logger.info(f"Received signal {signum}, shutting down...")
    sys.exit(0)


@app.command()
def main(
    work_duration: Annotated[
        Optional[int],
        typer.Option("--work", "-w", help="Work duration in minutes before break"),
    ] = None,
    break_duration: Annotated[
        Optional[int], typer.Option("--break", "-b", help="Break duration in minutes")
    ] = None,
    override_limit: Annotated[
        Optional[int],
        typer.Option("--overrides", "-o", help="Daily limit for manual overrides"),
    ] = None,
    config_file: Annotated[
        Optional[Path],
        typer.Option("--config", "-c", help="Path to configuration file"),
    ] = None,
    no_sound: Annotated[
        bool, typer.Option("--no-sound", help="Disable notification sounds")
    ] = False,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Enable verbose logging")
    ] = False,
    dry_run: Annotated[
        bool, typer.Option("--dry-run", help="Run without actually locking the screen")
    ] = False,
):
    """
    Start the Move Me timer to lock your screen at regular intervals.

    Move Me helps you take regular breaks by automatically locking your screen
    every 45 minutes (configurable) for 5 minutes (configurable). It includes
    manual override limits for flexibility during important work.
    """
    # Set up logging
    log_level = "DEBUG" if verbose else "INFO"
    logger = setup_logging(log_level)

    logger.info("Starting Move Me application")

    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Load configuration
        config_manager = ConfigManager()
        config = config_manager.load_config(config_file)

        # Override config with CLI arguments
        if work_duration is not None:
            config["work_duration_minutes"] = work_duration
        if break_duration is not None:
            config["break_duration_minutes"] = break_duration
        if override_limit is not None:
            config["daily_override_limit"] = override_limit
        if no_sound:
            config["notification_sound"] = False
        if dry_run:
            config["auto_lock_enabled"] = False
            logger.info("DRY RUN MODE: Screen locking disabled")

        # Validate configuration
        if not config_manager.validate_config(config):
            logger.error("Invalid configuration")
            raise typer.Exit(1)

        # Get state file path
        state_file_path = config_manager.get_state_file_path(config)

        # Create timer manager
        timer_manager = TimerManager(config, state_file_path)

        # Set up callbacks for user feedback
        def on_break_start():
            logger.info("Break started - screen locking.")

        def on_break_end():
            logger.info("Break ended - resuming work timer")

        def on_override_used():
            logger.info("Manual override used")

        timer_manager.set_callbacks(
            on_break_start=on_break_start,
            on_break_end=on_break_end,
            on_override_used=on_override_used,
        )

        # Display startup information
        typer.echo("🔒 Move Me Started")
        typer.echo(f"   Work duration: {config['work_duration_minutes']} minutes")
        typer.echo(f"   Break duration: {config['break_duration_minutes']} minutes")
        typer.echo(f"   Daily overrides: {config['daily_override_limit']}")
        typer.echo(
            f"   Notifications: {'enabled' if config.get('notification_sound', True) else 'silent'}"
        )
        if dry_run:
            typer.echo("   🧪 DRY RUN MODE - Screen will not be locked")
        typer.echo("")
        typer.echo("Press Ctrl+C to stop")
        typer.echo("")

        # Run the event loop
        asyncio.run(run_timer(timer_manager, logger))

    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Application error: {e}")
        raise typer.Exit(1)
    finally:
        logger.info("Move Me application stopped")


async def run_timer(timer_manager: TimerManager, logger) -> None:
    """Run the timer manager in an async loop."""
    last_status_time = 0.0

    try:
        # Start the timer asynchronously
        await timer_manager.start_async()

        # Wait for the timer to finish (it runs indefinitely)
        while timer_manager.is_running:
            await asyncio.sleep(1)

            # Display status updates every 60 seconds
            current_time = asyncio.get_event_loop().time()
            if (current_time - last_status_time) >= 60:
                _display_status(timer_manager, logger)
                last_status_time = current_time

    except asyncio.CancelledError:
        logger.info("Timer task cancelled")
        raise
    finally:
        if timer_manager.is_running:
            timer_manager.stop()


def _display_status(timer_manager: TimerManager, logger) -> None:
    """Display current timer status."""
    if timer_manager.is_in_break:
        remaining = timer_manager.time_remaining_in_break
        if remaining:
            logger.info(f"In break - {remaining.total_seconds():.0f}s remaining")
    else:
        next_break = timer_manager.time_until_next_break
        if next_break:
            minutes = next_break.total_seconds() / 60
            logger.info(f"Next break in {minutes:.0f} minutes")


@app.command()
def config(
    show: Annotated[
        bool, typer.Option("--show", help="Show current configuration")
    ] = False,
    reset: Annotated[
        bool, typer.Option("--reset", help="Reset configuration to defaults")
    ] = False,
):
    """Manage Move Me configuration."""
    config_manager = ConfigManager()

    if reset:
        # Reset to defaults
        default_config = config_manager._load_default_config()
        config_manager.save_config(default_config)
        typer.echo("Configuration reset to defaults")
        return

    if show:
        # Show current config
        config = config_manager.load_config()
        typer.echo(f"Config file: {config_manager.config_file}")
        typer.echo("Current configuration:")
        for key, value in config.items():
            typer.echo(f"  {key}: {value}")
        return

    typer.echo("Use --show to display configuration or --reset to reset to defaults")


@app.command()
def status():
    """Show current application status and statistics."""
    config_manager = ConfigManager()
    config = config_manager.load_config()
    state_file_path = config_manager.get_state_file_path(config)

    if not state_file_path.exists():
        typer.echo("No state file found. Run the application first.")
        return

    # We could load the StateManager here to show statistics
    # For now, just show basic info
    typer.echo("Move Me Status:")
    typer.echo(f"  Config file: {config_manager.config_file}")
    typer.echo(f"  State file: {state_file_path}")
    typer.echo(f"  Work duration: {config['work_duration_minutes']} minutes")
    typer.echo(f"  Break duration: {config['break_duration_minutes']} minutes")


if __name__ == "__main__":
    app()
