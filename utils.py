import logging
import os
import sys
import time
from pathlib import Path


def get_app_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


PROJECT_ROOT = get_app_root()
LOG_FILE_PATH = PROJECT_ROOT / "logs" / "organizer.log"
PID_FILE_PATH = Path("/tmp/auto-file-organizer.pid")
LOGGER_NAME = "auto_file_organizer"


def expand_path(path_like) -> Path:
    return Path(path_like).expanduser().resolve()


def get_extension(path_like) -> str:
    return Path(path_like).suffix.lower()


def configure_logging(log_to_file=False, log_file_path=LOG_FILE_PATH):
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()

    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", "%H:%M:%S")

    if log_to_file:
        log_path = Path(log_file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(log_path, encoding="utf-8")
    else:
        handler = logging.StreamHandler(sys.stdout)

    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


def get_logger():
    logger = logging.getLogger(LOGGER_NAME)
    if not logger.handlers:
        configure_logging()
    return logger


def log(message, level="INFO"):
    logger = get_logger()
    level_name = level.upper()
    logger.log(getattr(logging, level_name, logging.INFO), message)


def write_pid_file(pid, pid_file_path=PID_FILE_PATH):
    pid_path = Path(pid_file_path)
    pid_path.write_text(str(pid), encoding="utf-8")


def read_pid_file(pid_file_path=PID_FILE_PATH):
    pid_path = Path(pid_file_path)
    if not pid_path.exists():
        return None

    try:
        return int(pid_path.read_text(encoding="utf-8").strip())
    except ValueError:
        return None


def remove_pid_file(pid_file_path=PID_FILE_PATH):
    Path(pid_file_path).unlink(missing_ok=True)


def process_is_running(pid):
    if pid is None or pid <= 0:
        return False

    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def get_running_pid(pid_file_path=PID_FILE_PATH):
    pid = read_pid_file(pid_file_path)
    if pid is None:
        remove_pid_file(pid_file_path)
        return None

    if process_is_running(pid):
        return pid

    remove_pid_file(pid_file_path)
    return None


def wait_for_stable_file(path, checks=3, delay_seconds=0.5) -> bool:
    file_path = Path(path)
    previous_size = None
    stable_reads = 0
    max_attempts = max((checks * 4), 8)

    for _ in range(max_attempts):
        if not file_path.exists():
            return False

        try:
            current_size = file_path.stat().st_size
        except OSError:
            return False

        if current_size == previous_size:
            stable_reads += 1
        else:
            stable_reads = 0
            previous_size = current_size

        if stable_reads >= checks:
            return True

        time.sleep(delay_seconds)

    return False
