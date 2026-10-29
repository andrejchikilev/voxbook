"""Tests for the voxbook list command."""
from datetime import datetime, timezone

import pytest
from sqlmodel import Session, create_engine, select
from typer.testing import CliRunner

from voxbook.cli import app
from voxbook.library.models import Book, BookFile
from voxbook.playback.models import BookPlaybackState

runner = CliRunner()


@pytest.fixture
def fresh_db(tmp_path, monkeypatch):
    db_path = tmp_path / "voxbook.db"
    test_engine = create_engine(f"sqlite:///{db_path}")
    monkeypatch.setattr("voxbook.storage.db.DB_PATH", db_path)
    monkeypatch.setattr("voxbook.storage.db.engine", test_engine)
    monkeypatch.setattr("voxbook.playback.repository.engine", test_engine)
    monkeypatch.setattr("voxbook.cli.engine", test_engine)
    from voxbook.storage.db import init_db

    init_db()
    yield test_engine


def _add_book(session, title, durations):
    counter = len(session.exec(select(Book)).all()) + 1
    book = Book(title=title, path=f"/test/{counter}_{title}")
    session.add(book)
    session.commit()
    session.refresh(book)
    for index, duration in enumerate(durations, start=1):
        session.add(
            BookFile(
                book_id=book.id,
                path=f"/test/{counter}_{title}_{index}.mp3",
                index=index,
                duration=duration,
            )
        )
    session.commit()
    return book


def _add_state(engine, book_id, file_index, position, updated_at=None):
    from voxbook.playback.repository import PlaybackRepository

    repo = PlaybackRepository()
    repo.save_position(book_id, file_index, position, speed=1.0)
    if updated_at is not None:
        with Session(engine) as session:
            state = session.get(BookPlaybackState, book_id)
            state.updated_at = updated_at
            session.commit()


def _run_list(*args):
    return runner.invoke(app, ["list", *args])


class TestListFilters:
    def test_filter_not_started(self, fresh_db):
        engine = fresh_db
        with Session(engine) as session:
            _add_book(session, "Alpha", [100.0])
            _add_state(engine, 1, 1, 50.0)
            _add_book(session, "Beta", [100.0])

        result = _run_list("--filter", "not-started")
        assert result.exit_code == 0
        assert "Beta" in result.output
        assert "Alpha" not in result.output
        assert "not started" in result.output

    def test_filter_in_progress(self, fresh_db):
        engine = fresh_db
        with Session(engine) as session:
            _add_book(session, "Alpha", [100.0])
            _add_state(engine, 1, 1, 50.0)
            _add_book(session, "Beta", [100.0])

        result = _run_list("--filter", "in-progress")
        assert result.exit_code == 0
        assert "Alpha" in result.output
        assert "Beta" not in result.output
        assert "in progress" in result.output

    def test_filter_finished(self, fresh_db):
        engine = fresh_db
        with Session(engine) as session:
            _add_book(session, "Alpha", [100.0])
            _add_state(engine, 1, 1, 100.0)
            _add_book(session, "Beta", [100.0])

        result = _run_list("--filter", "finished")
        assert result.exit_code == 0
        assert "Alpha" in result.output
        assert "Beta" not in result.output
        assert "finished" in result.output


class TestListSorts:
    def test_sort_title(self, fresh_db):
        engine = fresh_db
        with Session(engine) as session:
            _add_book(session, "Zebra", [100.0])
            _add_book(session, "Apple", [100.0])

        result = _run_list("--sort", "title")
        assert result.exit_code == 0
        assert result.output.index("Apple") < result.output.index("Zebra")

    def test_sort_progress_descending(self, fresh_db):
        engine = fresh_db
        with Session(engine) as session:
            _add_book(session, "Low", [100.0])
            _add_state(engine, 1, 1, 20.0)
            _add_book(session, "High", [100.0])
            _add_state(engine, 2, 1, 80.0)

        result = _run_list("--sort", "progress")
        assert result.exit_code == 0
        assert result.output.index("80.0%") < result.output.index("20.0%")

    def test_sort_recent_descending(self, fresh_db):
        engine = fresh_db
        with Session(engine) as session:
            _add_book(session, "Old", [100.0])
            _add_state(engine, 1, 1, 10.0, datetime(2026, 10, 1, tzinfo=timezone.utc))
            _add_book(session, "New", [100.0])
            _add_state(engine, 2, 1, 10.0, datetime(2026, 10, 29, tzinfo=timezone.utc))

        result = _run_list("--sort", "recent")
        assert result.exit_code == 0
        assert result.output.index("New") < result.output.index("Old")


class TestListFilterAndSort:
    def test_filter_and_sort_combined(self, fresh_db):
        engine = fresh_db
        with Session(engine) as session:
            _add_book(session, "A", [100.0])
            _add_state(engine, 1, 1, 10.0)
            _add_book(session, "B", [100.0])
            _add_state(engine, 2, 1, 90.0)
            _add_book(session, "C", [100.0])

        result = _run_list("--filter", "in-progress", "--sort", "progress")
        assert result.exit_code == 0
        assert "C" not in result.output
        assert result.output.index("90.0%") < result.output.index("10.0%")
