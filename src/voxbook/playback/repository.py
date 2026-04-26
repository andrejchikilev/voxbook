from datetime import datetime, timezone

from sqlalchemy import desc
from sqlmodel import Session, select

from voxbook.playback.models import BookPlaybackState
from voxbook.storage.db import engine


class PlaybackRepository:
    def load_position(self, book_id: int) -> BookPlaybackState | None:
        with Session(engine) as session:
            return session.get(BookPlaybackState, book_id)

    def load_last_position(self) -> BookPlaybackState | None:
        with Session(engine) as session:
            return session.exec(
                select(BookPlaybackState).order_by(desc(BookPlaybackState.updated_at))
            ).first()

    def save_position(
        self,
        book_id: int,
        file_index: int,
        position: float,
        speed: float,
    ) -> None:
        with Session(engine) as session:
            state = session.get(BookPlaybackState, book_id)

            if state is None:
                state = BookPlaybackState(
                    book_id=book_id,
                    file_index=file_index,
                    position=position,
                    speed=speed,
                )
                session.add(state)
            else:
                state.file_index = file_index
                state.position = position
                state.speed = speed
                state.updated_at = datetime.now(timezone.utc)

            session.commit()
