# ------------------------------------------------------------------
#
# Additional helper functions for bookmarks
#
# ------------------------------------------------------------------
from datetime import datetime, timezone

from sqlalchemy import Engine
from sqlalchemy import or_ as sqlalchemy_or
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


class BookMatcher:
    """Criterion for selecting books during a purge operation."""

    def __init__(
        self,
        title_exact: str | None = None,
        title_ilike: str | None = None,
    ) -> None:
        self.title_exact = title_exact
        self.title_ilike = title_ilike

    def apply(self, statement):
        if self.title_exact is not None:
            statement = statement.where(Book.title == self.title_exact)
        if self.title_ilike is not None:
            statement = statement.where(Book.title.ilike(self.title_ilike))
        return statement


def _is_real_listening_state(state: BookPlaybackState | None) -> bool:
    """Return True if the state looks like genuine user progress."""
    if state is None:
        return False
    return state.position > 0 or state.file_index > 1


def purge_books_matching(
    session_or_engine: Session | Engine,
    matchers: list[BookMatcher],
) -> dict[str, int]:
    """
    Delete books matching any of the supplied criteria and their related rows.

    Safety guards:
    - Books with any of author, series, or narrator set are never removed.
    - Books with a playback state indicating real listening progress
      (position > 0 or file_index > 1) are never removed.
    - Matching is case-insensitive for ILIKE patterns.

    Uses remove_book for each target so deletion order stays consistent
    (BookFile -> Bookmark -> BookPlaybackState -> Book) and transactional.

    Returns a summary dict with keys: books, files, bookmarks, progress_states.
    If no books match, returns all zeros and does not delete anything.
    """
    target_session: Session | None = None
    own_session = False
    if isinstance(session_or_engine, Engine):
        target_session = Session(session_or_engine)
        own_session = True
    else:
        target_session = session_or_engine

    try:
        candidates = _collect_purge_candidates(target_session, matchers)

        books_removed = 0
        files_removed = 0
        bookmarks_removed = 0
        progress_removed = 0

        for book in candidates:
            assert book.id is not None

            if book.author or book.series or book.narrator:
                continue

            state = target_session.get(BookPlaybackState, book.id)
            if _is_real_listening_state(state):
                continue

            removed, files_count, bookmarks_count, progress = remove_book(book.id)
            if removed:
                books_removed += 1
                files_removed += files_count
                bookmarks_removed += bookmarks_count
                if progress:
                    progress_removed += 1

        return {
            "books": books_removed,
            "files": files_removed,
            "bookmarks": bookmarks_removed,
            "progress_states": progress_removed,
        }
    finally:
        if own_session and target_session is not None:
            target_session.close()


def _collect_purge_candidates(target_session: Session, matchers: list[BookMatcher]) -> list[Book]:
    statement = select(Book)
    if matchers:
        conditions = []
        for matcher in matchers:
            sub = select(Book.id)
            sub = matcher.apply(sub).subquery()
            # pylint: disable=no-member
            conditions.append(Book.id.in_(sub))
        statement = statement.where(sqlalchemy_or(*conditions))
    return list(target_session.exec(statement).all())
