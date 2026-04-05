import argparse
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

from autostart import (
    autostart_status,
    install_autostart,
    linux_service_enablement_status,
    linux_service_installed,
    linux_service_is_active,
    start_linux_service,
    stop_linux_service,
    uninstall_autostart,
)
from rules import RuleEngine, load_config
from utils import (
    LOG_FILE_PATH,
    configure_logging,
    expand_path,
    get_running_pid,
    log,
    process_is_running,
    remove_pid_file,
    write_pid_file,
    kill_all_organizer_processes,
)
from watcher import organize_existing_files, start_watcher


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Automatically organize files in a directory using watchdog events."
    )
    parser.add_argument(
        "--path",
        default="~/Downloads",
        help="Folder to watch. Defaults to ~/Downloads.",
    )
    parser.add_argument(
        "--start",
        action="store_true",
        help="Start the organizer in the background.",
    )
    parser.add_argument(
        "--stop",
        action="store_true",
        help="Stop the background organizer.",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show whether the background organizer is running.",
    )
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Run the organizer in the background.",
    )
    parser.add_argument(
        "--install-autostart",
        action="store_true",
        help="Install auto-start on boot for the current OS.",
    )
    parser.add_argument(
        "--uninstall-autostart",
        action="store_true",
        help="Remove auto-start on boot for the current OS.",
    )
    parser.add_argument(
        "--autostart-status",
        action="store_true",
        help="Show auto-start installation status for the current OS.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate moves without changing any files.",
    )
    parser.add_argument(
        "--config",
        help="Optional path to a custom JSON config file.",
    )
    parser.add_argument(
        "--run-service",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--install",
        action="store_true",
        help="Install the organizer to ~/.local/bin for global use.",
    )
    return parser


def load_runtime(args):
    watch_path = expand_path(args.path)
    if not watch_path.exists() or not watch_path.is_dir():
        log(f"Watch path does not exist or is not a directory: {watch_path}", level="ERROR")
        return None

    try:
        config = load_config(args.config)
    except (FileNotFoundError, ValueError) as exc:
        log(str(exc), level="ERROR")
        return None

    rule_engine = RuleEngine(
        rules=config["rules"],
        default_category=config["default_category"],
        ignored_extensions=config["ignored_extensions"],
    )
    return watch_path, config, rule_engine


def build_service_command(args):
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--run-service",
        "--path",
        str(expand_path(args.path)),
    ]
    if args.dry_run:
        command.append("--dry-run")
    if args.config:
        command.extend(["--config", str(expand_path(args.config))])
    return command


def report_status():
    if linux_service_installed():
        service_state = "running" if linux_service_is_active() else "stopped"
        enablement = linux_service_enablement_status()
        pid = get_running_pid()
        if pid is not None:
            log(
                f"Organizer service is {service_state} under systemd with PID {pid}. "
                f"Autostart: {enablement}. Logs: {LOG_FILE_PATH}"
            )
        else:
            log(
                f"Organizer service is {service_state} under systemd. "
                f"Autostart: {enablement}. Logs: {LOG_FILE_PATH}"
            )
        return 0

    pid = get_running_pid()
    if pid is None:
        log("Organizer is not running.")
        return 0

    log(f"Organizer is running with PID {pid}. Logs: {LOG_FILE_PATH}")
    return 0


def stop_background_service():
    stopped_any = False

    # 1. Stop systemd service if exists
    if linux_service_installed():
        if linux_service_is_active():
            if stop_linux_service():
                log("Stopped systemd service.")
                stopped_any = True

    # 2. Stop PID-based process
    pid = get_running_pid()
    if pid is not None:
        try:
            os.kill(pid, signal.SIGTERM)
            log(f"Sent stop signal to organizer process {pid}.")
            stopped_any = True
        except ProcessLookupError:
            log("Process already stopped.", level="WARNING")

    # 3. Kill ALL leftover processes (IMPORTANT FIX)
    kill_all_organizer_processes()

    # 4. Cleanup PID file
    remove_pid_file()

    if stopped_any:
        log("Organizer stopped.")
    else:
        log("Organizer is not running.")

    return 0

def start_background_service(args):
    if linux_service_installed():
        if linux_service_is_active():
            pid = get_running_pid()
            if pid is not None:
                log(f"Organizer service is already running with PID {pid}.")
            else:
                log("Organizer service is already running.")
            return 1

        if not start_linux_service():
            return 1

        for _ in range(30):
            if linux_service_is_active():
                pid = get_running_pid()
                if pid is not None:
                    log(f"Organizer service started with PID {pid}. Logs: {LOG_FILE_PATH}")
                else:
                    log(f"Organizer service started. Logs: {LOG_FILE_PATH}")
                return 0
            time.sleep(0.1)

        log("Organizer service did not become active within the timeout.", level="ERROR")
        return 1

    running_pid = get_running_pid()

    if running_pid is not None:
        log(f"Organizer is already running with PID {running_pid}.")
        return 1

    # Extra safety: prevent duplicate instances (python + binary)
    existing = subprocess.run(
        ["pgrep", "-f", "organizer-linux"],
        capture_output=True,
        text=True,
    )

    if existing.stdout.strip():
        log("Another organizer instance is already running.")
        return 1

    process = subprocess.Popen(
        build_service_command(args),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        cwd=str(Path(__file__).resolve().parent),
        start_new_session=True,
    )

    for _ in range(30):
        pid = get_running_pid()
        if pid is not None:
            log(f"Organizer started in background with PID {pid}. Logs: {LOG_FILE_PATH}")
            return 0

        if process.poll() is not None:
            break
        time.sleep(0.1)

    log(f"Failed to start background organizer. Check {LOG_FILE_PATH}.", level="ERROR")
    return 1


def run_service(args, log_to_file=False, manage_pid=False):
    configure_logging(log_to_file=log_to_file)

    # Prevent multiple service instances
    existing_pid = get_running_pid()
    if existing_pid is not None and existing_pid != os.getpid():
        log(f"Another organizer instance is already running with PID {existing_pid}. Exiting.")
        return 1

    runtime = load_runtime(args)
    if runtime is None:
        return 1

    watch_path, config, rule_engine = runtime

    try:
        observer = start_watcher(
            watch_path=watch_path,
            rule_engine=rule_engine,
            dry_run=args.dry_run,
            stability_checks=config["stability"]["checks"],
            stability_delay=config["stability"]["delay_seconds"],
        )
    except ModuleNotFoundError:
        log(
            "watchdog is not installed. Install it with: pip install watchdog",
            level="ERROR",
        )
        return 1

    if manage_pid:
        write_pid_file(os.getpid())
        log(f"Background organizer started with PID {os.getpid()}.")

    mode = "dry-run" if args.dry_run else "live"
    log(f"Scanning existing files in {watch_path} before live watching starts.")
    organized_count = organize_existing_files(
        watch_path=watch_path,
        rule_engine=rule_engine,
        dry_run=args.dry_run,
        stability_checks=config["stability"]["checks"],
        stability_delay=config["stability"]["delay_seconds"],
    )
    if organized_count:
        log(f"Initial scan organized {organized_count} file(s).")
    else:
        log("Initial scan found no top-level files to organize.")

    if log_to_file:
        log(f"Watching {watch_path} in {mode} mode.")
    else:
        log(f"Watching {watch_path} in {mode} mode. Press Ctrl+C to stop.")

    stop_requested = False

    def request_shutdown(signum=None, frame=None):
        nonlocal stop_requested
        if stop_requested:
            return
        stop_requested = True
        log("Stopping watcher...")
        observer.stop()

    signal.signal(signal.SIGINT, request_shutdown)
    signal.signal(signal.SIGTERM, request_shutdown)

    try:
        while observer.is_alive() and not stop_requested:
            time.sleep(1)
    except KeyboardInterrupt:
        request_shutdown()
    finally:
        observer.stop()
        observer.join()
        if manage_pid:
            remove_pid_file()

    return 0


def validate_command_args(args, parser):
    command_flags = [
        args.start,
        args.stop,
        args.status,
        args.daemon,
        args.install_autostart,
        args.uninstall_autostart,
        args.autostart_status,
    ]
    if sum(bool(flag) for flag in command_flags) > 1:
        parser.error("Use only one command flag at a time.")

    if args.stop and (args.start or args.status or args.daemon):
        parser.error("--stop cannot be combined with --start, --status, or --daemon.")
    if args.status and (args.start or args.stop or args.daemon):
        parser.error("--status cannot be combined with --start, --stop, or --daemon.")

def install_binary():
    import shutil

    if not getattr(sys, "frozen", False):
        log("Install is only supported for the compiled binary.", level="ERROR")
        return 1

    source_path = Path(sys.executable).resolve()
    target_dir = Path.home() / ".local" / "bin"
    target_path = target_dir / "organizer"

    try:
        target_dir.mkdir(parents=True, exist_ok=True)

        # Copy instead of move (safer)
        shutil.copy2(source_path, target_path)

        # Ensure executable permission
        target_path.chmod(0o755)

    except Exception as e:
        log(f"Installation failed: {e}", level="ERROR")
        return 1

    log(f"Installed successfully at {target_path}")

    log("You can now run:")
    print(f"\n  organizer --install-autostart\n")

    return 0

def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    validate_command_args(args, parser)

    if args.run_service:
        return run_service(args, log_to_file=True, manage_pid=True)

    configure_logging()
    
    if args.install:
        return install_binary()
    if args.stop:
        return stop_background_service()
    if args.status:
        return report_status()
    if args.start or args.daemon:
        return start_background_service(args)
    if args.install_autostart:
        return install_autostart(
            path=args.path,
            config_path=args.config,
            dry_run=args.dry_run,
        )
    if args.uninstall_autostart:
        return uninstall_autostart()
    if args.autostart_status:
        return autostart_status()

    return run_service(args)


if __name__ == "__main__":
    sys.exit(main())
