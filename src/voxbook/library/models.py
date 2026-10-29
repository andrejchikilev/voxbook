from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


class Book(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str
    path: str = Field(unique=True)
    author: str | None = None
    series: str | None = None
    narrator: str | None = None


class BookFile(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    book_id: int = Field(foreign_key="book.id")
    path: str = Field(unique=True)
    index: int
    duration: float = 0.0


class Bookmark(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    book_id: int = Field(foreign_key="book.id")
    file_index: int
    position: float
    note: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
