import shlex
import subprocess
import sys
from pathlib import Path

from utils import expand_path, get_app_root, log

LINUX_SERVICE_NAME = "auto-file-organizer.service"
MAC_PLIST_NAME = "com.auto-file-organizer.plist"
WINDOWS_TASK_NAME = "Auto File Organizer"


def build_runtime_command(path, config_path=None, dry_run=False):
    watch_path = str(expand_path(path))
    if getattr(sys, "frozen", False):
        command = [str(Path(sys.executable).resolve())]
    else:
        command = [sys.executable, str((Path(__file__).resolve().parent / "organizer.py"))]

    command.extend(["--run-service", "--path", watch_path])

    if dry_run:
        command.append("--dry-run")
    if config_path:
        command.extend(["--config", str(expand_path(config_path))])

    return command


def linux_service_path():
    return Path.home() / ".config" / "systemd" / "user" / LINUX_SERVICE_NAME


def linux_service_installed():
    return sys.platform.startswith("linux") and linux_service_path().exists()


def _run_linux_systemctl(arguments, capture_output=False):
    return subprocess.run(
        ["systemctl", "--user", *arguments],
        check=False,
        capture_output=capture_output,
        text=True,
    )


def linux_service_is_active():
    if not linux_service_installed():
        return False

    try:
        result = _run_linux_systemctl(["is-active", LINUX_SERVICE_NAME], capture_output=True)
    except FileNotFoundError:
        return False

    return result.stdout.strip() == "active"


def start_linux_service():
    if not linux_service_installed():
        return False

    try:
        result = _run_linux_systemctl(["start", LINUX_SERVICE_NAME])
    except FileNotFoundError:
        log("systemctl is not available to start the Linux autostart service.", level="ERROR")
        return False

    if result.returncode != 0:
        log("Failed to start the Linux autostart service.", level="ERROR")
        return False

    return True


def stop_linux_service():
    if not linux_service_installed():
        return False

    try:
        result = _run_linux_systemctl(["stop", LINUX_SERVICE_NAME])
    except FileNotFoundError:
        log("systemctl is not available to stop the Linux autostart service.", level="ERROR")
        return False

    if result.returncode != 0:
        log("Failed to stop the Linux autostart service.", level="ERROR")
        return False

    return True


def linux_service_enablement_status():
    if not linux_service_installed():
        return "not-installed"

    try:
        result = _run_linux_systemctl(["is-enabled", LINUX_SERVICE_NAME], capture_output=True)
    except FileNotFoundError:
        return "unknown"

    return result.stdout.strip() or result.stderr.strip() or "unknown"


def mac_plist_path():
    return Path.home() / "Library" / "LaunchAgents" / MAC_PLIST_NAME


def build_linux_service_content(command):
    return "\n".join(
        [
            "[Unit]",
            "Description=Auto File Organizer",
            "",
            "[Service]",
            f"ExecStart={shlex.join(command)}",
            f"WorkingDirectory={get_app_root()}",
            "Restart=always",
            "RestartSec=2",
            "",
            "[Install]",
            "WantedBy=default.target",
            "",
        ]
    )


def build_mac_plist_content(command):
    lines = [
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>",
        "<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" "
        "\"http://www.apple.com/DTDs/PropertyList-1.0.dtd\">",
        "<plist version=\"1.0\">",
        "<dict>",
        "    <key>Label</key>",
        "    <string>com.auto-file-organizer</string>",
        "    <key>ProgramArguments</key>",
        "    <array>",
    ]
    for part in command:
        lines.append(f"        <string>{part}</string>")
    lines.extend(
        [
            "    </array>",
            "    <key>RunAtLoad</key>",
            "    <true/>",
            "    <key>KeepAlive</key>",
            "    <true/>",
            "</dict>",
            "</plist>",
            "",
        ]
    )
    return "\n".join(lines)


def build_windows_task_command(command):
    return subprocess.list2cmdline(command)


def install_linux_autostart(command):
    service_path = linux_service_path()
    service_path.parent.mkdir(parents=True, exist_ok=True)
    service_path.write_text(build_linux_service_content(command), encoding="utf-8")

    try:
        subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
        subprocess.run(
            ["systemctl", "--user", "enable", "--now", service_path.name],
            check=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        log(
            "Systemd service file was created, but enabling it failed. "
            f"Run manually: systemctl --user daemon-reload && systemctl --user enable --now {service_path.name}. "
            f"Details: {exc}",
            level="WARNING",
        )
        return 0

    log(f"Installed and enabled Linux autostart service at {service_path}")
    return 0


def uninstall_linux_autostart():
    service_path = linux_service_path()
    try:
        subprocess.run(
            ["systemctl", "--user", "disable", "--now", service_path.name],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        subprocess.run(["systemctl", "--user", "daemon-reload"], check=False)
    except FileNotFoundError:
        pass

    if service_path.exists():
        service_path.unlink()
        log(f"Removed Linux autostart service at {service_path}")
    else:
        log("Linux autostart service was not installed.")
    return 0


def linux_autostart_status():
    service_path = linux_service_path()
    if not service_path.exists():
        log(f"Linux autostart is not installed. Expected service file: {service_path}")
        return 0

    log(f"Linux autostart service file exists: {service_path}")
    status = linux_service_enablement_status()
    log(f"systemd enablement status: {status}")
    log(f"systemd active state: {'active' if linux_service_is_active() else 'inactive'}")
    return 0


def install_mac_autostart(command):
    plist_path = mac_plist_path()
    plist_path.parent.mkdir(parents=True, exist_ok=True)
    plist_path.write_text(build_mac_plist_content(command), encoding="utf-8")

    try:
        subprocess.run(["launchctl", "load", plist_path], check=True)
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        log(
            "LaunchAgent plist was created, but loading it failed. "
            f"Run manually: launchctl load {plist_path}. Details: {exc}",
            level="WARNING",
        )
        return 0

    log(f"Installed macOS LaunchAgent at {plist_path}")
    return 0


def uninstall_mac_autostart():
    plist_path = mac_plist_path()
    try:
        subprocess.run(["launchctl", "unload", plist_path], check=False)
    except FileNotFoundError:
        pass

    if plist_path.exists():
        plist_path.unlink()
        log(f"Removed macOS LaunchAgent at {plist_path}")
    else:
        log("macOS LaunchAgent was not installed.")
    return 0


def mac_autostart_status():
    plist_path = mac_plist_path()
    if plist_path.exists():
        log(f"macOS LaunchAgent exists: {plist_path}")
    else:
        log(f"macOS LaunchAgent is not installed. Expected path: {plist_path}")
    return 0


def install_windows_autostart(command):
    task_command = build_windows_task_command(command)
    try:
        subprocess.run(
            [
                "schtasks",
                "/Create",
                "/SC",
                "ONLOGON",
                "/TN",
                WINDOWS_TASK_NAME,
                "/TR",
                task_command,
                "/F",
            ],
            check=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        log(
            "Failed to create Windows Task Scheduler entry. "
            f"Create it manually with command: {task_command}. Details: {exc}",
            level="ERROR",
        )
        return 1

    log(f"Installed Windows Task Scheduler entry: {WINDOWS_TASK_NAME}")
    return 0


def uninstall_windows_autostart():
    try:
        subprocess.run(
            ["schtasks", "/Delete", "/TN", WINDOWS_TASK_NAME, "/F"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        pass

    log(f"Removed Windows Task Scheduler entry: {WINDOWS_TASK_NAME}")
    return 0


def windows_autostart_status():
    try:
        result = subprocess.run(
            ["schtasks", "/Query", "/TN", WINDOWS_TASK_NAME],
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        log("Task Scheduler is not available on this system.", level="ERROR")
        return 1

    if result.returncode == 0:
        log(f"Windows Task Scheduler entry exists: {WINDOWS_TASK_NAME}")
    else:
        log(f"Windows Task Scheduler entry is not installed: {WINDOWS_TASK_NAME}")
    return 0


def install_autostart(path, config_path=None, dry_run=False):
    command = build_runtime_command(path=path, config_path=config_path, dry_run=dry_run)

    if sys.platform.startswith("linux"):
        return install_linux_autostart(command)
    if sys.platform == "darwin":
        return install_mac_autostart(command)
    if sys.platform.startswith("win"):
        return install_windows_autostart(command)

    log(f"Autostart installation is not implemented for platform: {sys.platform}", level="ERROR")
    return 1


def uninstall_autostart():
    if sys.platform.startswith("linux"):
        return uninstall_linux_autostart()
    if sys.platform == "darwin":
        return uninstall_mac_autostart()
    if sys.platform.startswith("win"):
        return uninstall_windows_autostart()

    log(f"Autostart removal is not implemented for platform: {sys.platform}", level="ERROR")
    return 1


def autostart_status():
    if sys.platform.startswith("linux"):
        return linux_autostart_status()
    if sys.platform == "darwin":
        return mac_autostart_status()
    if sys.platform.startswith("win"):
        return windows_autostart_status()

    log(f"Autostart status is not implemented for platform: {sys.platform}", level="ERROR")
    return 1
