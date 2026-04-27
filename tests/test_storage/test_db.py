"""Tests for storage database."""
from unittest.mock import patch

from voxbook.storage.db import DB_PATH, engine, init_db


class TestDatabase:
    """Tests for database operations."""

    def test_db_path_exists(self):
        """Test that DB_PATH is properly set."""
        assert DB_PATH.suffix == ".db"
        assert "voxbook" in str(DB_PATH)

    @patch("voxbook.storage.db.SQLModel.metadata.create_all")
    def test_init_db_creates_tables(self, mock_create_all):
        """Test that init_db creates all tables."""
        init_db()
        mock_create_all.assert_called_once_with(engine)

    def test_engine_created(self):
        """Test that engine is created with correct URL."""
        assert engine is not None
        assert "sqlite" in str(engine.url)
