from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


class BookPlaybackState(SQLModel, table=True):
    book_id: int = Field(primary_key=True, foreign_key="book.id")
    file_index: int = 1
    position: float = 0.0
    speed: float = 1.0
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
