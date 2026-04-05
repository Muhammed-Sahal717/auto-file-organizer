import subprocess
import sys
from pathlib import Path


def main():
    project_root = Path(__file__).resolve().parent
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--name",
        "organizer",
        "organizer.py",
    ]
    subprocess.run(command, cwd=project_root, check=True)


if __name__ == "__main__":
    main()
