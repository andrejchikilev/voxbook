"""Tests for library scanner."""
from pathlib import Path
from unittest.mock import Mock

from voxbook.library.scan_patterns.base import ScannedBook
from voxbook.library.scanner import match_books, save_scanned_book


class TestScanner:
    """Tests for library scanner functions."""

    def test_match_books_returns_empty_for_no_match(self, tmp_path: Path):
        """Test that match_books returns empty list when no pattern matches."""
        patterns = []
        result = match_books(tmp_path, patterns)
        assert result == []

    def test_match_books_returns_scanned_books(self, tmp_path: Path):
        """Test that match_books returns scanned books when pattern matches."""
        mock_pattern = Mock()
        scanned_book = ScannedBook(
            path=tmp_path / "book",
            title="Test Book",
            files=[]
        )
        mock_pattern.match.return_value = [scanned_book]

        result = match_books(tmp_path / "book", [mock_pattern])

        assert len(result) == 1
        assert result[0].title == "Test Book"
        mock_pattern.match.assert_called_once()

    def test_match_books_tries_all_patterns(self, tmp_path: Path):
        """Test that match_books tries all patterns in order."""
        mock_pattern1 = Mock()
        mock_pattern1.match.return_value = []

        mock_pattern2 = Mock()
        scanned_book = ScannedBook(path=tmp_path, title="Found", files=[])
        mock_pattern2.match.return_value = [scanned_book]

        result = match_books(tmp_path, [mock_pattern1, mock_pattern2])

        assert len(result) == 1
        mock_pattern1.match.assert_called_once()
        mock_pattern2.match.assert_called_once()


class TestSaveScannedBook:
    """Tests for save_scanned_book function."""

    def test_save_scanned_book_creates_new_book(self, mock_session: Mock):
        """Test creating a new book from scanned data."""
        mock_session.exec.return_value.first.return_value = None
        mock_session.exec.return_value.all.return_value = []

        # Mock refresh to set id on the book
        def mock_refresh(book):
            book.id = 1
        mock_session.refresh.side_effect = mock_refresh

        scanned_book = ScannedBook(
            path=Path("/test/book"),
            title="Test Book",
            files=[]
        )

        save_scanned_book(mock_session, scanned_book)

        mock_session.add.assert_called()
        mock_session.commit.assert_called_once()
