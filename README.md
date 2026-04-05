# Auto File Organizer

Auto File Organizer automatically cleans your Downloads folder by sorting files into folders like Images, PDFs, Videos, and more.

It runs silently in the background after setup and keeps your files organized without any manual effort.

## Quick Setup (Recommended)

Download the executable from the [Releases](../../releases) page.

### Linux / macOS

```bash
chmod +x organizer
./organizer --install-autostart
```

### Windows

Run `organizer.exe`, then:

```bash
organizer.exe --install-autostart
```

That's it. Your files will now be organized automatically.

## Quick Test

After installation, try:

```bash
touch ~/Downloads/test.jpg
```

You should see it move into:

```text
Downloads/Images/test.jpg
```

## For Users

### How It Works (Simple)

1. Run the installer command once
2. The app starts automatically in the background
3. Files in your Downloads folder are organized automatically
4. You do not need to keep starting it manually

### What It Does

- Organizes files already in the watched folder when the app starts
- Watches for newly created files and organizes them automatically
- Sorts files by extension using configurable rules
- Creates destination folders automatically
- Renames duplicates safely, such as `file.pdf` to `file(1).pdf`
- Ignores temporary download files like `.tmp` and `.crdownload`
- Waits for file size to stabilize before moving a file
- Supports background mode and auto-start on boot

### Default Categories

By default, files are sorted into:

- `Images`
- `PDFs`
- `Videos`
- `Documents`
- `Archives`
- `Others`

You can change these rules in `config.json`.

### Daily Commands

Start the organizer in the background:

```bash
./organizer --start
```

Check whether it is running:

```bash
./organizer --status
```

Stop it:

```bash
./organizer --stop
```

Install auto-start on boot:

```bash
./organizer --install-autostart
```

Check auto-start status:

```bash
./organizer --autostart-status
```

Remove auto-start:

```bash
./organizer --uninstall-autostart
```

### Uninstall

Stop the organizer:

```bash
./organizer --stop
```

Remove auto-start:

```bash
./organizer --uninstall-autostart
```

### Troubleshooting

If the organizer is not running:

```bash
./organizer --status
```

If needed, restart it:

```bash
./organizer --start
```

If you want to test without moving files:

```bash
./organizer --dry-run
```

### Example

If your Downloads folder contains:

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

### Logs

Background runs write logs to:

```bash
logs/organizer.log
```

This log file is created in the same folder where the executable is run.

## For Developers

### Requirements

- Python 3
- `watchdog`

If you want to build a standalone executable:

- `PyInstaller`

### Run From Source

Install dependencies:

```bash
pip install -r requirements.txt
```

Run in the foreground with the default folder:

```bash
python organizer.py
```

Watch a custom folder:

```bash
python organizer.py --path ~/Downloads
```

Use a custom config file:

```bash
python organizer.py --config /path/to/config.json
```

Simulate organizing without moving files:

```bash
python organizer.py --dry-run
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

### Configuration

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

### How Organizing Works

When the program starts, it:

1. Loads the configuration
2. Organizes files already in the top level of the watched folder
3. Starts watching for new files
4. Waits until a new file is stable
5. Moves the file into the correct folder

Files already inside subfolders are left alone.

### Testing

Run the tests with:

```bash
python -m unittest discover -s tests -v
```

### Project Files

- `organizer.py`: CLI entry point
- `watcher.py`: file watching and startup scan
- `mover.py`: safe file moving and duplicate handling
- `rules.py`: rule engine and config loading
- `utils.py`: logging, PID handling, and helpers
- `autostart.py`: OS-specific auto-start support

### Notes

- The organizer only moves top-level files in the watched folder during startup scan.
- Duplicate names are preserved by renaming instead of overwriting.
- Temporary download files are ignored until the real file appears.
- Files may not move immediately if they are still being downloaded.
