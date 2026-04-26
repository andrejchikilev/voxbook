# ------------------------------------------------------------------
#
# Additional helper functions for bookmarks
#
# ------------------------------------------------------------------
from datetime import datetime, timezone

from sqlmodel import Session, select

from voxbook.library.models import Bookmark
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
