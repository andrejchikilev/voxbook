from __future__ import annotations

import shutil
import time
from pathlib import Path
from typing import TYPE_CHECKING

from mpv import MPV

if TYPE_CHECKING:
    from voxbook.config import AppConfig


class MpvController:
    def __init__(self, config: AppConfig | None = None) -> None:
        self.config = config

    def _mpv_executable(self) -> str:
        if self.config is None:
            return "mpv"

        mpv_path = self.config.mpv_path
        if isinstance(mpv_path, Path):
            return str(mpv_path)

        expanded = Path(mpv_path).expanduser()
        if expanded.exists():
            return str(expanded)

        found = shutil.which(mpv_path)
        if found:
            return found

        return str(mpv_path)

    def create_player(self) -> MPV:
        mpv_executable = self._mpv_executable()
        return MPV(
            ytdl=False,
            vid="no",
            audio_display="no",
            input_default_bindings=False,
            input_vo_keyboard=False,
            mpv_location=mpv_executable,
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

    def get_volume(self, player: MPV) -> float | None:
        try:
            return player.volume
        except Exception:
            return None

    def set_volume(self, player: MPV, level: float) -> None:
        try:
            player.volume = level
        except Exception:
            pass

    def quit(self, player: MPV) -> None:
        try:
            player.quit()
        except Exception:
            pass
