import sys

from mpv import MPV
from rich.console import Console
from rich.control import Control, ControlType
from rich.text import Text
from sqlmodel import Session

from voxbook.helpers import format_seconds
from voxbook.library.models import Book
from voxbook.playback.mpv_controller import MpvController
from voxbook.playback.types import LogFn
from voxbook.storage.db import engine


class StatusRenderer:
    def __init__(
        self,
        log: LogFn,
        mpv: MpvController,
        console: Console | None = None,
    ) -> None:
        self.log = log
        self.mpv = mpv
        self.console = console or Console(file=sys.stdout)

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

        line = Text(f"{title} | file {file_index} | {format_seconds(position)} | {speed:.1f}x")

        if self.console.is_terminal:
            line.truncate(max(1, self.console.width - 1), overflow="ellipsis")
            self.console.control(
                Control(ControlType.CARRIAGE_RETURN),
                Control((ControlType.ERASE_IN_LINE, 2)),
            )
            self.console.print(line, end="", soft_wrap=True)
            self.console.file.flush()
            return

        self.console.print(line, end="\r", soft_wrap=True)
