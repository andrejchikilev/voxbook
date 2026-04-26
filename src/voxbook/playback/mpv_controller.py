import time

from mpv import MPV


class MpvController:
    def create_player(self) -> MPV:
        return MPV(
            ytdl=False,
            vid="no",
            audio_display="no",
            input_default_bindings=False,
            input_vo_keyboard=False,
        )

    def wait_until_loaded(self, player: MPV) -> None:
        for _ in range(50):
            try:
                if player.duration is not None:
                    return
            except Exception:
                return

            time.sleep(0.1)

    def toggle_pause(self, player: MPV) -> None:
        try:
            player.pause = not player.pause
        except Exception:
            pass

    def seek(self, player: MPV, seconds: float, reference: str) -> None:
        try:
            if player.duration is not None:
                player.seek(seconds, reference=reference, precision="exact")
        except Exception:
            pass

    def get_position(self, player: MPV) -> float | None:
        try:
            return player.time_pos
        except Exception:
            return None

    def is_idle(self, player: MPV) -> bool:
        try:
            return bool(player.idle_active)
        except Exception:
            return True

    def set_speed(self, player: MPV, speed: float) -> None:
        try:
            player.speed = speed
        except Exception:
            pass

    def quit(self, player: MPV) -> None:
        try:
            player.quit()
        except Exception:
            pass
