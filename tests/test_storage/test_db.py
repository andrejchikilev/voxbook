"""Tests for storage database."""
from unittest.mock import patch

from voxbook.storage.db import _current_db_path, engine, get_db_path, init_db


class TestDatabase:
    """Tests for database operations."""

    def test_db_path_exists(self):
        """Test that DB_PATH is properly set."""
        db_path = get_db_path()
        assert db_path.suffix == ".db"
        assert "voxbook" in str(db_path)

    @patch("voxbook.storage.db.SQLModel.metadata.create_all")
    def test_init_db_creates_tables(self, mock_create_all):
        """Test that init_db creates all tables."""
        init_db()
        mock_create_all.assert_called_once_with(engine)

    def test_engine_created(self):
        """Test that engine is created with correct URL."""
        assert engine is not None
        assert "sqlite" in str(engine.url)

    def test_get_db_path_returns_path(self, monkeypatch, tmp_path):
        """Test get_db_path reflects config changes."""
        config_path = tmp_path / "config.toml"
        config_path.write_text(f'db_path = "{tmp_path / "custom.db"}"\n')
        monkeypatch.setenv("VOXBOOK_DB_PATH", str(tmp_path / "custom.db"))

        assert get_db_path() == tmp_path / "custom.db"
        assert _current_db_path() == tmp_path / "custom.db"
