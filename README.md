# Auto File Organizer

Auto File Organizer is a small desktop automation tool that watches a folder such as `Downloads` and sorts files into folders like `Images`, `PDFs`, `Videos`, `Documents`, and `Archives`.

It is event-driven, which means it reacts to file system events instead of scanning in a loop. That keeps CPU usage low while still organizing files automatically.

## What It Does

- Organizes files already in the watched folder when the app starts
- Watches for newly created files and organizes them automatically
- Sorts files by extension using configurable rules
- Creates destination folders automatically
- Renames duplicates safely, such as `file.pdf` to `file(1).pdf`
- Ignores temporary download files like `.tmp` and `.crdownload`
- Waits for file size to stabilize before moving a file
- Supports foreground mode, background mode, and boot auto-start

## Default Categories

By default, files are sorted into:

- `Images`
- `PDFs`
- `Videos`
- `Documents`
- `Archives`
- `Others`

You can change these rules in [config.json](/home/sahal/Projects/auto-file-organizer/config.json).

## Requirements

- Python 3
- `watchdog`

If you want to build a standalone executable:

- `PyInstaller`

## Installation

### Run From Source

1. Open a terminal in the project folder.
2. Create and activate a virtual environment if you want one.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

### Build an Executable

```bash
pip install -r requirements-dev.txt
python build_executable.py
```

On Linux and macOS, the executable will be created at:

```bash
dist/organizer
```

On Windows, it will be:

```bash
dist\organizer.exe
```

## Quick Start

Run in the foreground with the default folder:

```bash
python organizer.py
```

Watch a custom folder:

```bash
python organizer.py --path ~/Downloads
```

Simulate organizing without moving files:

```bash
python organizer.py --dry-run
```

If you built the executable:

```bash
./dist/organizer
```

## Background Commands

Start the organizer in the background:

```bash
python organizer.py --start
```

Check whether it is running:

```bash
python organizer.py --status
```

Stop it:

```bash
python organizer.py --stop
```

The executable supports the same commands:

```bash
./dist/organizer --start
./dist/organizer --status
./dist/organizer --stop
```

## Auto-Start on Boot

Install auto-start for the current operating system:

```bash
python organizer.py --install-autostart
```

Check auto-start status:

```bash
python organizer.py --autostart-status
```

Remove auto-start:

```bash
python organizer.py --uninstall-autostart
```

On Linux, this creates a `systemd` user service.

## Configuration

The default configuration file looks like this:

```json
{
  "rules": {
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg"],
    "PDFs": [".pdf"],
    "Videos": [".mp4", ".mov", ".avi", ".mkv", ".webm"],
    "Documents": [".doc", ".docx", ".txt", ".rtf", ".odt"],
    "Archives": [".zip", ".rar", ".7z", ".tar", ".gz"]
  },
  "default_category": "Others",
  "ignored_extensions": [".tmp", ".crdownload", ".swp", ".part"],
  "stability": {
    "checks": 3,
    "delay_seconds": 0.5
  }
}
```

Use a custom config file like this:

```bash
python organizer.py --config /path/to/config.json
```

## How Organizing Works

When the program starts, it:

1. Loads the configuration
2. Organizes files already in the top level of the watched folder
3. Starts watching for new files
4. Waits until a new file is stable
5. Moves the file into the correct folder

Files already inside subfolders are left alone.

## Logs

Foreground runs log to the terminal.

Background runs log to:

```bash
logs/organizer.log
```

## Example

If your watched folder contains:

```text
Downloads/
  photo.jpg
  report.pdf
  movie.mp4
  notes.txt
  archive.zip
  unknown.xyz
```

After organizing, it becomes:

```text
Downloads/
  Images/photo.jpg
  PDFs/report.pdf
  Videos/movie.mp4
  Documents/notes.txt
  Archives/archive.zip
  Others/unknown.xyz
```

## Testing

Run the tests with:

```bash
python -m unittest discover -s tests -v
```

## Project Files

- [organizer.py](/home/sahal/Projects/auto-file-organizer/organizer.py): CLI entry point
- [watcher.py](/home/sahal/Projects/auto-file-organizer/watcher.py): file watching and startup scan
- [mover.py](/home/sahal/Projects/auto-file-organizer/mover.py): safe file moving and duplicate handling
- [rules.py](/home/sahal/Projects/auto-file-organizer/rules.py): rule engine and config loading
- [utils.py](/home/sahal/Projects/auto-file-organizer/utils.py): logging, PID handling, and helpers
- [autostart.py](/home/sahal/Projects/auto-file-organizer/autostart.py): OS-specific auto-start support

## Notes

- The organizer only moves top-level files in the watched folder during startup scan.
- Duplicate names are preserved by renaming instead of overwriting.
- Temporary download files are ignored until the real file appears.
