# ------------------------------------------------------------------
#
# Additional helper functions for bookmarks
#
# ------------------------------------------------------------------
from datetime import datetime, timezone

from sqlmodel import Session, select

from voxbook.library.models import Book, BookFile, Bookmark
from voxbook.playback.models import BookPlaybackState
from voxbook.storage.db import engine


def create_bookmark(
    book_id: int,
    file_index: int,
    position: float,
    note: str | None = None,
) -> Bookmark:
    with Session(engine) as session:
        bookmark = Bookmark(
            book_id=book_id,
            file_index=file_index,
            position=position,
            note=note,
            created_at=datetime.now(timezone.utc),
        )
        session.add(bookmark)
        session.commit()
        session.refresh(bookmark)
        return bookmark


def list_bookmarks(book_id: int) -> list[Bookmark]:
    with Session(engine) as session:
        return list(
            session.exec(
                select(Bookmark)
                .where(Bookmark.book_id == book_id)
                .order_by(Bookmark.file_index, Bookmark.position)
            ).all()
        )


def get_bookmark(bookmark_id: int) -> Bookmark | None:
    with Session(engine) as session:
        return session.get(Bookmark, bookmark_id)


def delete_bookmark(bookmark_id: int) -> bool:
    with Session(engine) as session:
        bookmark = session.get(Bookmark, bookmark_id)

        if bookmark is None:
            return False

        session.delete(bookmark)
        session.commit()
        return True


def remove_book(book_id: int) -> tuple[bool, int, int, bool]:
    """
    Remove a book and its related rows in a single transaction.

    Deletion order: BookFile -> Bookmark -> BookPlaybackState -> Book.
    Returns a tuple of (removed, files_count, bookmarks_count, progress_removed).
    If the book does not exist, returns (False, 0, 0, False) without deleting anything.

    --keep-progress is intentionally not implemented: BookPlaybackState.book_id is
    the primary key and references book.id, so keeping progress would leave an
    orphaned row once the book is deleted.
    """
    with Session(engine) as session:
        book = session.get(Book, book_id)
        if book is None:
            return False, 0, 0, False

        files = list(
            session.exec(select(BookFile).where(BookFile.book_id == book_id)).all()
        )
        bookmarks = list(
            session.exec(select(Bookmark).where(Bookmark.book_id == book_id)).all()
        )
        state = session.get(BookPlaybackState, book_id)

        files_count = len(files)
        bookmarks_count = len(bookmarks)

        for book_file in files:
            session.delete(book_file)
        for bookmark in bookmarks:
            session.delete(bookmark)
        if state is not None:
            session.delete(state)
            progress_removed = True
        else:
            progress_removed = False

        session.delete(book)
        session.commit()

        return True, files_count, bookmarks_count, progress_removed
