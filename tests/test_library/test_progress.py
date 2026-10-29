"""Tests for library progress helpers."""
from datetime import datetime, timezone

import pytest

from voxbook.library.models import BookFile
from voxbook.library.progress import book_progress, book_updated_at
from voxbook.playback.models import BookPlaybackState


def make_book_file(index: int, duration: float) -> BookFile:
    return BookFile(id=index, book_id=1, path=f"/test/{index}.mp3", index=index, duration=duration)


def make_state(
    file_index: int,
    position: float,
    updated_at: datetime | None = None,
) -> BookPlaybackState:
    return BookPlaybackState(
        book_id=1,
        file_index=file_index,
        position=position,
        speed=1.0,
        updated_at=updated_at or datetime.now(timezone.utc),
    )


class TestBookProgress:
    """Tests for book_progress helper."""

    def test_no_state_not_started(self):
        files = [make_book_file(1, 100.0)]
        status, position, total = book_progress(files, None)
        assert status == "not started"
        assert position == 0.0
        assert total == 100.0

    def test_zero_position_not_started(self):
        files = [make_book_file(1, 100.0)]
        state = make_state(1, 0.0)
        status, position, total = book_progress(files, state)
        assert status == "not started"
        assert position == 0.0
        assert total == 100.0

    def test_in_progress_middle(self):
        files = [make_book_file(1, 100.0)]
        state = make_state(1, 50.0)
        status, position, total = book_progress(files, state)
        assert status == "in progress"
        assert position == 50.0
        assert total == 100.0

    def test_finished_exact_end(self):
        files = [make_book_file(1, 100.0)]
        state = make_state(1, 100.0)
        status, position, total = book_progress(files, state)
        assert status == "finished"
        assert position == 100.0
        assert total == 100.0

    def test_finished_within_tolerance(self):
        files = [make_book_file(1, 100.0)]
        state = make_state(1, 99.2)
        status, position, total = book_progress(files, state)
        assert status == "finished"
        assert position == pytest.approx(99.2)
        assert total == 100.0

    def test_finished_multi_file(self):
        files = [make_book_file(1, 100.0), make_book_file(2, 50.0)]
        state = make_state(2, 50.0)
        status, position, total = book_progress(files, state)
        assert status == "finished"
        assert position == 150.0
        assert total == 150.0

    def test_in_progress_second_file(self):
        files = [make_book_file(1, 100.0), make_book_file(2, 50.0)]
        state = make_state(2, 20.0)
        status, position, total = book_progress(files, state)
        assert status == "in progress"
        assert position == 120.0
        assert total == 150.0

    def test_zero_total_not_started(self):
        files = [make_book_file(1, 0.0)]
        state = make_state(1, 0.0)
        status, position, total = book_progress(files, state)
        assert status == "not started"
        assert position == 0.0
        assert total == 0.0


class TestBookUpdatedAt:
    """Tests for book_updated_at helper."""

    def test_none_returns_epoch(self):
        result = book_updated_at(None)
        assert result == datetime.min.replace(tzinfo=timezone.utc)

    def test_state_returns_updated_at(self):
        now = datetime(2026, 10, 29, 12, 0, 0, tzinfo=timezone.utc)
        state = make_state(1, 0.0, updated_at=now)
        assert book_updated_at(state) == now
