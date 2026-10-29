from datetime import datetime, timezone
from typing import Literal

from voxbook.library.models import BookFile
from voxbook.playback.models import BookPlaybackState

FINISHED_TOLERANCE_SECONDS = 1.0

BookStatus = Literal["not started", "in progress", "finished"]


def book_progress(
    files: list[BookFile],
    state: BookPlaybackState | None,
) -> tuple[BookStatus, float, float]:
    """Return (status, current_position, total_duration) for a book."""
    total_duration = sum(book_file.duration for book_file in files)

    if not state or not files:
        return "not started", 0.0, total_duration

    previous_duration = sum(
        book_file.duration for book_file in files if book_file.index < state.file_index
    )
    book_position = previous_duration + state.position

    if total_duration <= 0.0:
        return "not started", book_position, total_duration

    if book_position <= 0.0:
        return "not started", book_position, total_duration

    if book_position >= total_duration - FINISHED_TOLERANCE_SECONDS:
        return "finished", book_position, total_duration

    return "in progress", book_position, total_duration


def book_updated_at(state: BookPlaybackState | None) -> datetime:
    """Return updated_at for sorting by recent, or epoch for not started books."""
    if state is None:
        return datetime.min.replace(tzinfo=timezone.utc)

    return state.updated_at
