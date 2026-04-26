# VoxBook

VoxBook is a CLI audiobook player with smart library scanning, playback state persistence, and flexible folder structure support.

> Repository: https://github.com/andrejchikilev/voxbook

## ✨ Features

- 📚 Automatic library scanning
- 🧠 Multiple folder structure patterns
- ▶️ Playback via `mpv`
- ⏯️ Pause, seek, playback speed control
- 💾 Automatic progress saving
- 🔖 Bookmarks
- 🔄 Resume last playback
- 📊 Live playback status

---

## 📋 Requirements

VoxBook depends on the following tools:

### Python environment

- [`uv`](https://github.com/astral-sh/uv) — fast Python package manager and virtualenv tool

Install `uv`:

```bash
pip install uv
```
or (recommended):

```bash
curl -Ls https://astral.sh/uv/install.sh | sh
```

---

## 📦 Installation

```bash
git clone git@github.com:andrejchikilev/voxbook.git
cd voxbook

uv venv
uv sync
```

Install `mpv`:

```bash
sudo apt install mpv
```

---

## 🚀 Usage

### Scan library

```bash
voxbook scan ~/Audiobooks
```

### List books

```bash
voxbook list
```

### Play book

```bash
voxbook play <book_id>
```

### Resume last book

```bash
voxbook resume
```

### Bookmarks

```bash
voxbook bookmarks <book_id>
voxbook goto-bookmark <bookmark_id>
voxbook delete-bookmark <bookmark_id>
```

### Reset progress

```bash
voxbook reset-progress <book_id>
```

---

## 🎧 Playback controls

| Key | Action |
|-----|--------|
| space | pause/play |
| ← / → | seek |
| n | next file |
| p | previous file |
| > | increase speed |
| < | decrease speed |
| = | reset speed |
| s | show status |
| b | bookmark |
| q | quit |

---

## ⚙️ Storage

SQLite DB:

```
~/.local/share/voxbook/voxbook.db
```
---

## 🚧 TODO

- TUI interface
- Volume control
- Chapter support
- Sync
- Smarter scanning

---

## 📄 License

MIT
