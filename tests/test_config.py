"""Tests for config module."""
from pathlib import Path

from voxbook.storage.db import DB_PATH


class TestConfig:
    """Tests for config module."""

    def test_db_path_default(self):
        """Test default database path."""
        assert DB_PATH == Path.home() / ".local/share/voxbook/voxbook.db"

    def test_db_path_expanded(self):
        """Test that DB_PATH is properly expanded."""
        assert DB_PATH.is_absolute()
        assert ".local/share/voxbook" in str(DB_PATH)
