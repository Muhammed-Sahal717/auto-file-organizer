# Auto File Organizer

Auto File Organizer automatically sorts files in a folder into categories like Images, PDFs, Videos, and more.

After setup, it runs in the background and organizes files as they appear.

---

## Download

Download the latest version from the **Releases** page.

---

## Quick Setup (Linux)

After downloading:

```bash
cd ~/Downloads
chmod +x organizer-linux
./organizer-linux --install-autostart
```

That’s it. The organizer will now run automatically in the background.

---

## Use a Different Folder

By default, it watches your Downloads folder.
---
To organize another folder:

```bash
cd ~/Downloads
./organizer-linux --install-autostart --path ~/Desktop
```

---

## Check Status

```bash
./organizer-linux --status
```

---

## Stop

```bash
./organizer-linux --stop
```

---

## Remove (Uninstall)

```bash
./organizer-linux --uninstall-autostart
```

---

## What It Does

* Moves files into folders like `Images`, `PDFs`, `Videos`, etc.
* Creates folders automatically if needed
* Renames duplicates safely (`file(1).jpg`)
* Ignores temporary download files
* Waits for files to finish downloading before moving them

---

## Example

Before:

```
Downloads/
  photo.jpg
  report.pdf
  video.mp4
```

After:

```
Downloads/
  Images/photo.jpg
  PDFs/report.pdf
  Videos/video.mp4
```

---

## Notes

* Only files in the top level of the folder are organized
* Files may not move immediately while they are still downloading

---

## Platform Support

* Linux: Available
* Windows: Coming soon
* macOS: Coming soon
