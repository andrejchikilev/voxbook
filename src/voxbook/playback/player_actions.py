from mpv import MPV

from voxbook.helpers import format_seconds
from voxbook.library.repository import create_bookmark
from voxbook.playback.context import PlaybackContext
from voxbook.playback.mpv_controller import MpvController
from voxbook.playback.status_renderer import StatusRenderer
from voxbook.playback.types import LogFn


class PlayerActions:
    def __init__(
        self,
        context: PlaybackContext,
        log: LogFn,
        mpv: MpvController,
        status_renderer: StatusRenderer,
    ) -> None:
        self.context = context
        self.log = log
        self.mpv = mpv
        self.status_renderer = status_renderer

    def quit(self) -> None:
        self.context.stop_event.set()

    def show_status(self) -> None:
        player = self._get_current_player()

        if (
            player is None
            or self.context.current_book_id is None
            or self.context.current_file_index is None
        ):
            return

        self.status_renderer.print_status(
            player=player,
            book_id=self.context.current_book_id,
            file_index=self.context.current_file_index,
            speed=self.context.playback_speed,
        )

    def create_bookmark(self) -> None:
        player = self._get_current_player()

        if (
            player is None
            or self.context.current_book_id is None
            or self.context.current_file_index is None
        ):
            return

        position = self.mpv.get_position(player)

        if position is None:
            self.log("[BOOKMARK] Cannot get current position")
            return

        create_bookmark(
            book_id=self.context.current_book_id,
            file_index=self.context.current_file_index,
            position=position,
        )

        self.log(
            f"[BOOKMARK] saved | "
            f"file={self.context.current_file_index} | "
            f"pos={format_seconds(position)}"
        )

    def next_file(self) -> None:
        self.context.skip_to_next = True

    def previous_file(self) -> None:
        self.context.skip_to_previous = True

    def toggle_pause(self) -> None:
        player = self._get_current_player()
        if player is not None:
            self.mpv.toggle_pause(player)

    def seek_forward(self) -> None:
        player = self._get_current_player()
        if player is not None:
            self.mpv.seek(player, 30, reference="relative")

    def seek_backward(self) -> None:
        player = self._get_current_player()
        if player is not None:
            self.mpv.seek(player, -15, reference="relative")

    def speed_up(self) -> None:
        self.set_speed(min(3.0, self.context.playback_speed + 0.1))

    def speed_down(self) -> None:
        self.set_speed(max(0.5, self.context.playback_speed - 0.1))

    def speed_reset(self) -> None:
        self.set_speed(1.0)

    def set_speed(self, speed: float) -> None:
        player = self._get_current_player()

        self.context.playback_speed = speed

        if player is not None:
            self.mpv.set_speed(player, speed)

        self.log(f"Speed: {speed:.1f}x")

    def _get_current_player(self) -> MPV | None:
        with self.context.player_lock:
            return self.context.current_player
