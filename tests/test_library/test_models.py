"""Tests for library models."""
from voxbook.library.models import Book, BookFile


class TestBook:
    """Tests for Book model."""

    def test_book_creation(self):
        """Test creating a Book instance."""
        book = Book(
            title="Test Book",
            path="/test/path"
        )
        assert book.title == "Test Book"
        assert book.path == "/test/path"
        assert book.id is None

    def test_book_default_values(self):
        """Test default values for Book fields."""
        book = Book(title="Test", path="/test")
        assert book.id is None
        assert book.title == "Test"


class TestBookFile:
    """Tests for BookFile model."""

    def test_book_file_creation(self):
        """Test creating a BookFile instance."""
        book_file = BookFile(
            path="/test/audio.mp3",
            index=0,
            duration=3600,
            book_id=1
        )
        assert book_file.path == "/test/audio.mp3"
        assert book_file.index == 0
        assert book_file.duration == 3600
        assert book_file.book_id == 1
