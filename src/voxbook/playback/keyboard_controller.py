import threading
from collections.abc import Callable

import readchar


class KeyboardController:
    def __init__(
        self,
        stop_event: threading.Event,
        on_quit: Callable[[], None],
        on_status: Callable[[], None],
        on_bookmark: Callable[[], None],
        on_next: Callable[[], None],
        on_previous: Callable[[], None],
        on_pause: Callable[[], None],
        on_seek_forward: Callable[[], None],
        on_seek_backward: Callable[[], None],
        on_speed_up: Callable[[], None],
        on_speed_down: Callable[[], None],
        on_speed_reset: Callable[[], None],
    ) -> None:
        self.stop_event = stop_event
        self.on_quit = on_quit
        self.on_status = on_status
        self.on_bookmark = on_bookmark
        self.on_next = on_next
        self.on_previous = on_previous
        self.on_pause = on_pause
        self.on_seek_forward = on_seek_forward
        self.on_seek_backward = on_seek_backward
        self.on_speed_up = on_speed_up
        self.on_speed_down = on_speed_down
        self.on_speed_reset = on_speed_reset

    def run(self) -> None:
        while not self.stop_event.is_set():
            try:
                key = readchar.readkey()
            except KeyboardInterrupt:
                self.on_quit()
                return
            except Exception:
                continue

            if key == "q":
                self.on_quit()
            elif key == "s":
                self.on_status()
            elif key == "b":
                self.on_bookmark()
            elif key == "n":
                self.on_next()
            elif key == "p":
                self.on_previous()
            elif key == " ":
                self.on_pause()
            elif key == readchar.key.RIGHT:
                self.on_seek_forward()
            elif key == readchar.key.LEFT:
                self.on_seek_backward()
            elif key == ">":
                self.on_speed_up()
            elif key == "<":
                self.on_speed_down()
            elif key == "=":
                self.on_speed_reset()
