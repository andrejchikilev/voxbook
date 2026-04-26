import threading

from mpv import MPV


class PlaybackContext:
    def __init__(self) -> None:
        self.stop_event = threading.Event()
        self.player_lock = threading.Lock()

        self.current_player: MPV | None = None

        self.last_position = 0.0
        self.skip_to_next = False
        self.skip_to_previous = False

        self.current_book_id: int | None = None
        self.current_file_index: int | None = None
        self.current_book_title: str | None = None

        self.playback_speed = 1.0

    def get_player(self) -> MPV | None:
        with self.player_lock:
            return self.current_player

    def set_player(self, player: MPV | None) -> None:
        with self.player_lock:
            self.current_player = player
