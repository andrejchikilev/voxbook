"""Tests for storage database."""
from unittest.mock import patch

from sqlalchemy import create_engine, text

from voxbook.storage.db import _current_db_path, _ensure_columns, engine, get_db_path, init_db


class TestDatabase:
    """Tests for database operations."""

    def test_db_path_exists(self):
        """Test that DB_PATH is properly set."""
        db_path = get_db_path()
        assert db_path.suffix == ".db"
        assert "voxbook" in str(db_path)

    @patch("voxbook.storage.db.SQLModel.metadata.create_all")
    @patch("voxbook.storage.db._ensure_columns")
    def test_init_db_creates_tables(self, mock_ensure_columns, mock_create_all):
        """Test that init_db creates all tables and ensures columns."""
        init_db()
        mock_create_all.assert_called_once_with(engine)
        mock_ensure_columns.assert_called_once_with(engine)

    @patch("voxbook.storage.db.DB_PATH")
    def test_ensure_columns_adds_missing_columns(self, mock_db_path, tmp_path):
        """Test that _ensure_columns adds missing columns to an existing table."""
        db_file = tmp_path / "legacy.db"
        mock_db_path.return_value = db_file

        legacy_engine = create_engine(f"sqlite:///{db_file}")

        with legacy_engine.connect() as connection:
            connection.execute(
                text("CREATE TABLE book (id INTEGER PRIMARY KEY, title TEXT, path TEXT)")
            )
            connection.execute(
                text(
                    "CREATE TABLE bookplaybackstate ("
                    "book_id INTEGER PRIMARY KEY, file_index INTEGER, "
                    "position FLOAT, speed FLOAT, updated_at DATETIME)"
                )
            )
            connection.commit()

        _ensure_columns(legacy_engine)

        with legacy_engine.connect() as connection:
            book_columns = {
                row[1] for row in connection.execute(text("PRAGMA table_info(book)")).fetchall()
            }
            playback_columns = {
                row[1]
                for row in connection.execute(
                    text("PRAGMA table_info(bookplaybackstate)")
                ).fetchall()
            }

        assert {"author", "series", "narrator"} <= book_columns
        assert "volume" in playback_columns

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
