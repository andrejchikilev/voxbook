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

## ⚙️ Configuration

VoxBook reads settings from `~/.config/voxbook/config.toml` (flat keys, no nested tables).
Environment variables with the `VOXBOOK_` prefix override TOML values.

Example `~/.config/voxbook/config.toml`:

```toml
db_path = "~/.local/share/voxbook/voxbook.db"
mpv_path = "mpv"
seek_step_seconds = 30
speed_step = 0.1
speed_min = 0.5
speed_max = 3.0
```

Supported variables:

| TOML key | Environment variable | Default |
|----------|----------------------|---------|
| `db_path` | `VOXBOOK_DB_PATH` | `~/.local/share/voxbook/voxbook.db` |
| `mpv_path` | `VOXBOOK_MPV_PATH` | `mpv` |
| `seek_step_seconds` | `VOXBOOK_SEEK_STEP_SECONDS` | `30` |
| `speed_step` | `VOXBOOK_SPEED_STEP` | `0.1` |
| `speed_min` | `VOXBOOK_SPEED_MIN` | `0.5` |
| `speed_max` | `VOXBOOK_SPEED_MAX` | `3.0` |

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
