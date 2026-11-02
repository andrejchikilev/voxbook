# VoxBook

VoxBook is a CLI audiobook player with smart library scanning, playback state persistence, and flexible folder structure support.

**Version:** 0.2.0

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

VoxBook requires Python 3.14 or later and [`uv`](https://github.com/astral-sh/uv), a Python package and environment manager. Install `mpv` for audiobook playback.

Install `uv` with `pip`:

```bash
pip install uv
```
Or use the installer (recommended):

```bash
curl -Ls https://astral.sh/uv/install.sh | sh
```

---

## 📦 Installation

```bash
git clone https://github.com/andrejchikilev/voxbook.git
cd voxbook
uv sync
```

Install `mpv`:

```bash
sudo apt install mpv
```

---

## 🚀 Usage

### Manage libraries

```bash
voxbook scan ~/Audiobooks
voxbook rescan
voxbook roots
voxbook roots --remove ~/Audiobooks
```

`scan` adds and scans a directory. `rescan` scans all configured roots. `roots` lists configured roots; use `--remove` to remove one.

### Find and inspect books

```bash
voxbook list
voxbook list --filter in-progress --sort recent
voxbook search "author or title"
voxbook book-info <book_id>
voxbook files <book_id>
voxbook status <book_id>
```

`list` accepts `--filter not-started|in-progress|finished` and `--sort title|progress|recent`.

### Playback and progress

```bash
voxbook play <book_id>
voxbook resume
voxbook goto <book_id> 1:23:45
voxbook set-speed <book_id> 1.25
voxbook volume 60
```

`goto` accepts a position in seconds, `minutes:seconds`, or `hours:minutes:seconds`. `volume` shows or changes the volume of the active player (0–100).
`set-speed` accepts values from 0.5 to 3.0.

### Bookmarks and metadata

```bash
voxbook bookmarks <book_id>
voxbook goto-bookmark <bookmark_id>
voxbook delete-bookmark <bookmark_id>
voxbook set-book <book_id> --author "Author" --series "Series" --narrator "Narrator"
```

### Remove data

```bash
voxbook reset-progress <book_id>
voxbook remove-book <book_id>
voxbook purge --title-glob 'Sample*'
voxbook reset-db
```

`reset-progress`, `remove-book`, and `reset-db` ask for confirmation by default; add `--force` to skip confirmation. `purge` previews matching books and asks for confirmation; use `--yes` to skip it. `reset-db` deletes the database and all library data.

Run `voxbook --help` or `voxbook <command> --help` for the complete command and option reference.

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
| ] | increase volume |
| [ | decrease volume |
| s | show status |
| b | bookmark |
| q | quit |

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

`mpv_path` is the path or command name of the `mpv` binary. VoxBook checks that the file exists or is available on `PATH` before playback and logs a warning if it cannot be found. This value is not passed to mpv as an option.

For a disposable CLI database, set `VOXBOOK_DB_PATH` for that command:

```sh
VOXBOOK_DB_PATH=/tmp/voxbook-test.db uv run voxbook list
```

Use a different path for each manual test run if you want a fresh database. Pytest
sets this variable automatically to an isolated temporary database for the whole run.

## 🚧 TODO

- TUI interface
- Chapter support
- Sync
- Smarter scanning

---

## 📄 License

MIT
