"""Tests for config module."""
from pathlib import Path

from voxbook.config import AppConfig, load_config


class TestConfig:
    """Tests for config module."""

    def test_default_values(self, monkeypatch, tmp_path):
        """Test default configuration values."""
        monkeypatch.setenv("HOME", str(tmp_path))
        config = load_config(Path("/nonexistent/config.toml"))

        assert config.db_path == tmp_path / ".local/share/voxbook/voxbook.db"
        assert config.mpv_path == "mpv"
        assert config.seek_step_seconds == 30
        assert config.speed_step == 0.1
        assert config.speed_min == 0.5
        assert config.speed_max == 3.0

    def test_load_from_toml(self, tmp_path):
        """Test loading configuration from TOML file."""
        config_path = tmp_path / "config.toml"
        config_path.write_text(
            'db_path = "/tmp/voxbook.db"\n'
            'mpv_path = "/usr/local/bin/mpv"\n'
            "seek_step_seconds = 60\n"
            "speed_step = 0.25\n"
            "speed_min = 0.25\n"
            "speed_max = 4.0\n"
        )

        config = load_config(config_path)

        assert config.db_path == Path("/tmp/voxbook.db")
        assert config.mpv_path == "/usr/local/bin/mpv"
        assert config.seek_step_seconds == 60
        assert config.speed_step == 0.25
        assert config.speed_min == 0.25
        assert config.speed_max == 4.0

    def test_env_override(self, monkeypatch, tmp_path):
        """Test environment variables override TOML and defaults."""
        config_path = tmp_path / "config.toml"
        config_path.write_text(
            'db_path = "/tmp/voxbook.db"\n'
            "seek_step_seconds = 60\n"
            "speed_step = 0.25\n"
        )

        monkeypatch.setenv("VOXBOOK_DB_PATH", "/env/voxbook.db")
        monkeypatch.setenv("VOXBOOK_MPV_PATH", "/env/mpv")
        monkeypatch.setenv("VOXBOOK_SEEK_STEP_SECONDS", "90")
        monkeypatch.setenv("VOXBOOK_SPEED_STEP", "0.5")
        monkeypatch.setenv("VOXBOOK_SPEED_MIN", "0.2")
        monkeypatch.setenv("VOXBOOK_SPEED_MAX", "5.0")

        config = load_config(config_path)

        assert config.db_path == Path("/env/voxbook.db")
        assert config.mpv_path == "/env/mpv"
        assert config.seek_step_seconds == 90
        assert config.speed_step == 0.5
        assert config.speed_min == 0.2
        assert config.speed_max == 5.0

    def test_default_config_path(self, monkeypatch, tmp_path):
        """Test loading from default config path."""
        config_dir = tmp_path / ".config/voxbook"
        config_dir.mkdir(parents=True)
        config_path = config_dir / "config.toml"
        config_path.write_text('db_path = "/default/voxbook.db"\n')

        monkeypatch.setenv("HOME", str(tmp_path))

        config = load_config()

        assert config.db_path == Path("/default/voxbook.db")

    def test_tilde_expansion(self, monkeypatch, tmp_path):
        """Test tilde expansion in paths."""
        monkeypatch.setenv("HOME", str(tmp_path))
        config_path = tmp_path / "config.toml"
        config_path.write_text('db_path = "~/custom/voxbook.db"\n')

        config = load_config(config_path)

        assert config.db_path == tmp_path / "custom/voxbook.db"

    def test_app_config_dataclass(self):
        """Test AppConfig dataclass creation."""
        config = AppConfig(
            db_path=Path("/test/db"),
            mpv_path="mpv",
            seek_step_seconds=45,
            speed_step=0.2,
            speed_min=0.5,
            speed_max=3.0,
        )

        assert config.db_path == Path("/test/db")
        assert config.seek_step_seconds == 45
