import threading
import time
from pathlib import Path

from voxbook.library.models import BookFile
from voxbook.playback.context import PlaybackContext
from voxbook.playback.keyboard_controller import KeyboardController
from voxbook.playback.mpv_controller import MpvController
from voxbook.playback.player_actions import PlayerActions
from voxbook.playback.repository import PlaybackRepository
from voxbook.playback.status_renderer import StatusRenderer
from voxbook.playback.types import LogFn, PlaybackResult


class PlayerService:
    def __init__(
        self,
        log: LogFn | None = None,
        context: PlaybackContext | None = None,
        mpv: MpvController | None = None,
        status_renderer: StatusRenderer | None = None,
        playback_repository: PlaybackRepository | None = None,
    ) -> None:
        self.log = log or (lambda message: None)

        # 1. Base state
        self.context = context or PlaybackContext()

        # 2. Then controllers that depend on the state
        self.mpv = mpv or MpvController()
        self.status_renderer = status_renderer or StatusRenderer(log=self.log, mpv=self.mpv)
        self.playback_repository = playback_repository or PlaybackRepository()

        # 3. Then actions
        self.actions = PlayerActions(
            context=self.context,
            log=self.log,
            mpv=self.mpv,
            status_renderer=self.status_renderer,
        )

        # 4. And only then keyboard
        self.keyboard = KeyboardController(
            stop_event=self.context.stop_event,
            on_quit=self.actions.quit,
            on_status=self.actions.show_status,
            on_bookmark=self.actions.create_bookmark,
            on_next=self.actions.next_file,
            on_previous=self.actions.previous_file,
            on_pause=self.actions.toggle_pause,
            on_seek_forward=self.actions.seek_forward,
            on_seek_backward=self.actions.seek_backward,
            on_speed_up=self.actions.speed_up,
            on_speed_down=self.actions.speed_down,
            on_speed_reset=self.actions.speed_reset,
        )

    def play_book(self, book_id: int, files: list[BookFile], book_title: str) -> None:
        if not files:
            self.log("Book has no audio files")
            return

        self.context.current_book_title = book_title
        self.context.stop_event.clear()
        self.context.last_position = 0.0

        key_thread = threading.Thread(
            target=self.keyboard.run,
            daemon=True,
        )
        key_thread.start()

        state = self.playback_repository.load_position(book_id)
        self.context.playback_speed = state.speed if state else 1.0
        start_index = state.file_index if state else 1
        start_position = state.position if state else 0.0

        files_by_index = {file.index: file for file in files}
        current_index = start_index

        while current_index in files_by_index and not self.context.stop_event.is_set():
            book_file = files_by_index[current_index]

            result = self._play_single_book_file(
                book_id=book_id,
                file_index=current_index,
                file_path=Path(book_file.path),
                start_position=start_position,
            )

            if result in {"completed", "next"}:
                start_position = 0.0
                current_index += 1

            elif result == "previous":
                start_position = 0.0
                current_index = max(1, current_index - 1)

            else:
                break

    def _play_single_book_file(
        self,
        book_id: int,
        file_index: int,
        file_path: Path,
        start_position: float = 0.0,
    ) -> PlaybackResult:
        player = self.mpv.create_player()

        completed = False
        result: PlaybackResult = "stopped"

        self.context.skip_to_next = False
        self.context.skip_to_previous = False

        self.context.last_position = start_position
        self.context.current_book_id = book_id
        self.context.current_file_index = file_index

        with self.context.player_lock:
            self.context.current_player = player

        self.log(f"Playing file {file_index}: {file_path}")

        try:
            player.play(str(file_path))
            self.mpv.wait_until_loaded(player)
            self.mpv.set_speed(player, self.context.playback_speed)

            if start_position:
                self.log(f"Resuming from {start_position:.2f} seconds...")
                self.mpv.seek(player, start_position, reference="absolute")

            while not self.context.stop_event.is_set():
                time.sleep(1)

                self.status_renderer.render_status_line(
                    player=player,
                    book_title=self.context.current_book_title,
                    file_index=self.context.current_file_index,
                    speed=self.context.playback_speed,
                )

                if self.context.skip_to_next:
                    result = "next"
                    self.playback_repository.save_position(
                        book_id, file_index + 1, 0.0, speed=self.context.playback_speed
                    )
                    break

                if self.context.skip_to_previous:
                    result = "previous"
                    previous_index = max(1, file_index - 1)
                    self.playback_repository.save_position(
                        book_id, previous_index, 0.0, speed=self.context.playback_speed
                    )
                    break

                pos = self.mpv.get_position(player)
                if pos is not None:
                    self.context.last_position = pos
                    self.playback_repository.save_position(
                        book_id, file_index, pos, speed=self.context.playback_speed
                    )

                if self.mpv.is_idle(player):
                    completed = True
                    result = "completed"
                    self.playback_repository.save_position(
                        book_id, file_index + 1, 0.0, speed=self.context.playback_speed
                    )
                    break

        except KeyboardInterrupt:
            self.log("Stopping playback...")
            self.context.stop_event.set()
            result = "stopped"

        finally:
            if not completed and result == "stopped":
                self.playback_repository.save_position(
                    book_id,
                    file_index,
                    self.context.last_position,
                    speed=self.context.playback_speed,
                )

            with self.context.player_lock:
                if self.context.current_player is player:
                    self.context.current_player = None

            try:
                player.quit()
                print()
            except Exception:
                pass

        return result
