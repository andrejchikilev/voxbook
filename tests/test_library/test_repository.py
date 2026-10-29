"""Tests for library repository helpers."""
from unittest.mock import MagicMock, patch

import pytest
from sqlmodel import Session, SQLModel, create_engine, select

from voxbook.library.models import Book, BookFile, Bookmark
from voxbook.library.repository import remove_book
from voxbook.playback.models import BookPlaybackState


@pytest.fixture
def in_memory_engine():
    """Create an isolated in-memory SQLite engine."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def db_session(in_memory_engine):
    """Yield a session bound to the isolated engine and roll it back after each test."""
    with Session(in_memory_engine) as session:
        yield session
        session.rollback()


def _book_id(book: Book) -> int:
    assert book.id is not None
    return book.id


def test_remove_book_deletes_related_rows(db_session, in_memory_engine):
    """Removing a book deletes its files, bookmarks and playback state."""
    book = Book(title="Test Book", path="/books/test")
    db_session.add(book)
    db_session.commit()
    db_session.refresh(book)

    book_file = BookFile(
        book_id=_book_id(book), path="/books/test/01.mp3", index=1, duration=100.0
    )
    bookmark = Bookmark(book_id=_book_id(book), file_index=1, position=10.0)
    state = BookPlaybackState(book_id=_book_id(book), file_index=1, position=10.0, speed=1.2)
    db_session.add(book_file)
    db_session.add(bookmark)
    db_session.add(state)
    db_session.commit()

    with patch("voxbook.library.repository.engine", in_memory_engine):
        removed, files_count, bookmarks_count, progress_removed = remove_book(_book_id(book))

    assert removed is True
    assert files_count == 1
    assert bookmarks_count == 1
    assert progress_removed is True

    with Session(in_memory_engine) as check_session:
        assert check_session.get(Book, _book_id(book)) is None
        assert check_session.exec(
            select(BookFile).where(BookFile.book_id == _book_id(book))
        ).first() is None
        assert check_session.exec(
            select(Bookmark).where(Bookmark.book_id == _book_id(book))
        ).first() is None
        assert check_session.get(BookPlaybackState, _book_id(book)) is None


def test_remove_book_without_related_rows(db_session, in_memory_engine):
    """Removing a book with no related rows still removes the book."""
    book = Book(title="Empty Book", path="/books/empty")
    db_session.add(book)
    db_session.commit()
    db_session.refresh(book)

    with patch("voxbook.library.repository.engine", in_memory_engine):
        removed, files_count, bookmarks_count, progress_removed = remove_book(_book_id(book))

    assert removed is True
    assert files_count == 0
    assert bookmarks_count == 0
    assert progress_removed is False

    with Session(in_memory_engine) as check_session:
        assert check_session.get(Book, _book_id(book)) is None


def test_remove_book_returns_false_for_missing_book(in_memory_engine):
    """Removing a non-existent book returns False and deletes nothing."""
    with patch("voxbook.library.repository.engine", in_memory_engine):
        result = remove_book(999)

    assert result == (False, 0, 0, False)


def test_remove_book_is_atomic(db_session, in_memory_engine):
    """A failure during commit leaves all rows in place."""
    book = Book(title="Atomic Book", path="/books/atomic")
    db_session.add(book)
    db_session.commit()
    db_session.refresh(book)

    book_file = BookFile(
        book_id=_book_id(book), path="/books/atomic/01.mp3", index=1, duration=100.0
    )
    db_session.add(book_file)
    db_session.commit()

    mock_session = MagicMock()
    mock_session.__enter__ = MagicMock(return_value=mock_session)
    mock_session.__exit__ = MagicMock(return_value=None)
    mock_session.get.return_value = book
    mock_session.exec.side_effect = db_session.exec
    mock_session.commit.side_effect = RuntimeError("database locked")

    with patch("voxbook.library.repository.Session") as mock_session_cls:
        mock_session_cls.return_value = mock_session
        with pytest.raises(RuntimeError, match="database locked"):
            remove_book(_book_id(book))

    with Session(in_memory_engine) as check_session:
        assert check_session.get(Book, _book_id(book)) is not None
        assert check_session.exec(
            select(BookFile).where(BookFile.book_id == _book_id(book))
        ).first() is not None
