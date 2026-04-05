# Auto File Organizer

Auto File Organizer automatically organizes files in a selected folder (e.g., `Downloads`) into categories such as Images, PDFs, Videos, and more.

Once set up, it runs in the background and requires no manual intervention.

---

## 🚀 Features

* Automatically sorts files into categorized folders
* Creates folders if they do not exist
* Safely renames duplicate files (e.g., `file.jpg` → `file(1).jpg`)
* Ignores temporary/incomplete download files (`.tmp`, `.crdownload`, etc.)
* Waits until downloads are complete before organizing
* Uses event-driven file watching (low CPU usage)

---

## 📥 Download

Download the latest Linux binary from the **Releases** page.

---

## ⚙️ Quick Setup (Linux)

After downloading:

```bash
cd ~/Downloads
chmod +x organizer-linux
./organizer-linux --install
organizer --install-autostart
```

The organizer will now run automatically in the background.

---

## 📂 Use a Different Folder

By default, the organizer watches your `Downloads` folder.

To organize another folder (e.g., `Desktop`):

```bash
organizer --install-autostart --path ~/Desktop
```

---

## 🧰 Common Commands

### Check status

```bash
organizer --status
```

### Start the organizer

```bash
organizer --start
```

### Stop the organizer

```bash
organizer --stop
```

### Restart (if needed)

```bash
organizer --stop
organizer --start
```

---

## 🗑️ Uninstall

```bash
organizer --stop
organizer --uninstall-autostart
rm ~/.local/bin/organizer
```

---

## 📌 Example

### Before

```
Downloads/
  photo.jpg
  report.pdf
  video.mp4
```

### After

```
Downloads/
  Images/photo.jpg
  PDFs/report.pdf
  Videos/video.mp4
```

---

## ℹ️ Notes

* Only top-level files in the folder are organized
* Files may not move immediately while still downloading
* Runs as a background service using `systemd` (Linux)

---

## 💻 Platform Support

* Linux: ✅ Available
* Windows: ⏳ Coming soon
* macOS: ⏳ Coming soon
