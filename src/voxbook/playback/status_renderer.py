from mpv import MPV
from sqlmodel import Session

from voxbook.helpers import format_seconds
from voxbook.library.models import Book
from voxbook.playback.mpv_controller import MpvController
from voxbook.playback.types import LogFn
from voxbook.storage.db import engine


class StatusRenderer:
    def __init__(self, log: LogFn, mpv: MpvController) -> None:
        self.log = log
        self.mpv = mpv

    def print_status(
        self,
        player: MPV,
        book_id: int,
        file_index: int,
        speed: float,
    ) -> None:
        with Session(engine) as session:
            book = session.get(Book, book_id)

        title = book.title if book else "Unknown book"
        position = self.mpv.get_position(player) or 0.0

        self.log(
            f"[STATUS] {title} | "
            f"file={file_index} | "
            f"pos={format_seconds(position)} | "
            f"speed={speed:.1f}x"
        )

    def render_status_line(
        self,
        player: MPV,
        book_title: str | None,
        file_index: int | None,
        speed: float,
    ) -> None:
        position = self.mpv.get_position(player) or 0.0
        title = book_title or "Unknown"

        line = f"{title} | file {file_index} | {format_seconds(position)} | {speed:.1f}x"

        print(f"\r{line.ljust(120)}", end="", flush=True)
