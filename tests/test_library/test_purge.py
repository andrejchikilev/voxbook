"""Tests for purge_books_matching and the purge CLI command."""
from unittest.mock import patch

import pytest
from sqlmodel import Session, SQLModel, create_engine, select
from typer.testing import CliRunner

from voxbook.cli import app
from voxbook.library.models import Book, BookFile, Bookmark
from voxbook.library.repository import BookMatcher, purge_books_matching
from voxbook.playback.models import BookPlaybackState

runner = CliRunner()


@pytest.fixture
def in_memory_engine():
    """Create an isolated in-memory SQLite engine."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(bind=engine)
    return engine


@pytest.fixture
def db_session(in_memory_engine):
    """Yield a session bound to the isolated engine and roll it back after each test."""
    session = Session(bind=in_memory_engine)
    try:
        yield session
    finally:
        session.rollback()
        session.close()


def _add_book(session, title, author=None, series=None, narrator=None):
    book = Book(
        title=title,
        path=f"/books/{title}",
        author=author,
        series=series,
        narrator=narrator,
    )
    session.add(book)
    session.commit()
    session.refresh(book)
    return book


def _add_file(session, book, path=None, index=1):
    book_file = BookFile(
        book_id=book.id, path=path or f"/books/{book.title}/01.mp3", index=index, duration=100.0
    )
    session.add(book_file)
    session.commit()
    return book_file


def _add_state(session, book, file_index=1, position=0.0):
    state = BookPlaybackState(book_id=book.id, file_index=file_index, position=position)
    session.add(state)
    session.commit()
    return state


def _add_bookmark(session, book):
    bookmark = Bookmark(book_id=book.id, file_index=1, position=10.0)
    session.add(bookmark)
    session.commit()
    return bookmark


class TestPurgeByGlob:
    def test_purge_by_glob_removes_matching_junk(self, db_session, in_memory_engine):
        junk = _add_book(db_session, "goto book")
        real = _add_book(db_session, "Master and Margarita")
        _add_file(db_session, junk)

        junk_id = junk.id
        real_id = real.id

        with patch("voxbook.library.repository.engine", in_memory_engine):
            summary = purge_books_matching(
                in_memory_engine, [BookMatcher(title_ilike="goto%")]
            )

        assert summary == {"books": 1, "files": 1, "bookmarks": 0, "progress_states": 0}

        with Session(in_memory_engine) as check:
            assert check.get(Book, junk_id) is None
            assert check.get(Book, real_id) is not None

    def test_purge_preserves_books_with_author(self, db_session, in_memory_engine):
        book = _add_book(db_session, "goto bad", author="Test Author")
        _add_file(db_session, book)

        with patch("voxbook.library.repository.engine", in_memory_engine):
            summary = purge_books_matching(
                in_memory_engine, [BookMatcher(title_ilike="goto%")]
            )

        assert summary == {"books": 0, "files": 0, "bookmarks": 0, "progress_states": 0}

        with Session(in_memory_engine) as check:
            assert check.get(Book, book.id) is not None

    def test_purge_preserves_books_with_real_progress(self, db_session, in_memory_engine):
        book = _add_book(db_session, "goto book 2")
        _add_file(db_session, book)
        _add_state(db_session, book, file_index=1, position=5.0)

        with patch("voxbook.library.repository.engine", in_memory_engine):
            summary = purge_books_matching(
                in_memory_engine, [BookMatcher(title_ilike="goto%")]
            )

        assert summary == {"books": 0, "files": 0, "bookmarks": 0, "progress_states": 0}

    def test_purge_zero_pattern_returns_zeros(self, in_memory_engine):
        with patch("voxbook.library.repository.engine", in_memory_engine):
            summary = purge_books_matching(
                in_memory_engine, [BookMatcher(title_ilike="no-such-pattern%")]
            )

        assert summary == {"books": 0, "files": 0, "bookmarks": 0, "progress_states": 0}

    def test_purge_is_atomic(self, db_session, in_memory_engine):
        books = [_add_book(db_session, f"atomic junk {index}") for index in range(2)]
        for book in books:
            _add_file(db_session, book)

        original_delete = Session.delete
        deleted = 0

        def fail_after_first_delete(session, instance):
            nonlocal deleted
            if isinstance(instance, Book):
                deleted += 1
                if deleted == 2:
                    raise RuntimeError("simulated failure")
            return original_delete(session, instance)

        with patch("voxbook.library.repository.engine", in_memory_engine):
            with patch(
                "sqlmodel.Session.delete",
                fail_after_first_delete,
            ):
                with pytest.raises(RuntimeError, match="simulated failure"):
                    purge_books_matching(in_memory_engine, [BookMatcher(title_ilike="atomic%")])

        with Session(in_memory_engine) as check:
            for book in books:
                assert check.get(Book, book.id) is not None
                assert check.exec(
                    select(BookFile).where(BookFile.book_id == book.id)
                ).first() is not None


class TestPurgeCLI:
    def test_preview_excludes_guarded_books(self, in_memory_engine, monkeypatch):
        monkeypatch.setattr("voxbook.cli.engine", in_memory_engine)
        monkeypatch.setattr("voxbook.library.repository.engine", in_memory_engine)

        with Session(in_memory_engine) as session:
            _add_book(session, "goto real", author="Real Author")
            junk = _add_book(session, "goto junk")
            _add_file(session, junk)

        result = runner.invoke(app, ["purge", "--title-glob", "goto*"], input="y\n")

        assert result.exit_code == 0
        assert "goto real" not in result.output
        assert "Delete 1 book(s)" in result.output
        assert "Purged: 1 book(s)" in result.output

    def test_purge_dry_run_asks_before_delete(self, in_memory_engine, monkeypatch):
        monkeypatch.setattr("voxbook.cli.engine", in_memory_engine)
        monkeypatch.setattr("voxbook.library.repository.engine", in_memory_engine)

        with Session(in_memory_engine) as session:
            junk = _add_book(session, "goto bad")
            _add_file(session, junk)

        result = runner.invoke(app, ["purge", "--title-glob", "goto*"], input="y\n")

        assert result.exit_code == 0
        assert "goto bad" in result.output
        assert "Delete 1 book(s)" in result.output
        assert "Purged: 1 book(s)" in result.output

    def test_purge_no_glob_shows_hint(self, in_memory_engine, monkeypatch):
        monkeypatch.setattr("voxbook.cli.engine", in_memory_engine)

        result = runner.invoke(app, ["purge"])

        assert result.exit_code == 0
        assert "--title-glob" in result.output

    def test_purge_cancelled(self, in_memory_engine, monkeypatch):
        monkeypatch.setattr("voxbook.cli.engine", in_memory_engine)
        monkeypatch.setattr("voxbook.library.repository.engine", in_memory_engine)

        with Session(in_memory_engine) as session:
            junk = _add_book(session, "goto book")
            _add_file(session, junk)
            junk_id = junk.id

        result = runner.invoke(app, ["purge", "--title-glob", "goto*"], input="n\n")

        assert result.exit_code == 0
        assert "Cancelled" in result.output
        with Session(in_memory_engine) as check:
            assert check.get(Book, junk_id) is not None

    def test_purge_yes_flag_skips_confirm(self, in_memory_engine, monkeypatch):
        monkeypatch.setattr("voxbook.cli.engine", in_memory_engine)
        monkeypatch.setattr("voxbook.library.repository.engine", in_memory_engine)

        with Session(in_memory_engine) as session:
            junk = _add_book(session, "goto book")
            _add_file(session, junk)
            junk_id = junk.id

        result = runner.invoke(app, ["purge", "--title-glob", "goto*", "--yes"])

        assert result.exit_code == 0
        assert "Purged: 1 book(s)" in result.output
        with Session(in_memory_engine) as check:
            assert check.get(Book, junk_id) is None
