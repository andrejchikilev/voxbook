"""Tests for storage database."""
from unittest.mock import patch

from sqlalchemy import create_engine, text

from voxbook.storage.db import DB_PATH, _ensure_columns, engine, init_db


class TestDatabase:
    """Tests for database operations."""

    def test_db_path_exists(self):
        """Test that DB_PATH is properly set."""
        assert DB_PATH.suffix == ".db"
        assert "voxbook" in str(DB_PATH)

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
            connection.commit()

        _ensure_columns(legacy_engine)

        with legacy_engine.connect() as connection:
            columns = {
                row[1] for row in connection.execute(text("PRAGMA table_info(book)")).fetchall()
            }

        assert "author" in columns
        assert "series" in columns
        assert "narrator" in columns

    def test_engine_created(self):
        """Test that engine is created with correct URL."""
        assert engine is not None
        assert "sqlite" in str(engine.url)
