from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_DB_PATH_DEFAULT = "~/.local/share/voxbook/voxbook.db"
_CONFIG_DIR_DEFAULT = "~/.config/voxbook"
_CONFIG_FILE_NAME = "config.toml"

_MP_PATH_DEFAULT = "mpv"

_SEEK_STEP_SECONDS_DEFAULT = 30
_SPEED_STEP_DEFAULT = 0.1
_SPEED_MIN_DEFAULT = 0.5
_SPEED_MAX_DEFAULT = 3.0


@dataclass
class AppConfig:
    db_path: Path
    mpv_path: Path | str
    seek_step_seconds: int
    speed_step: float
    speed_min: float
    speed_max: float


def _default_config() -> AppConfig:
    return AppConfig(
        db_path=Path(_DB_PATH_DEFAULT).expanduser(),
        mpv_path=_MP_PATH_DEFAULT,
        seek_step_seconds=_SEEK_STEP_SECONDS_DEFAULT,
        speed_step=_SPEED_STEP_DEFAULT,
        speed_min=_SPEED_MIN_DEFAULT,
        speed_max=_SPEED_MAX_DEFAULT,
    )


def _merge_config(base: AppConfig, overrides: dict[str, Any]) -> AppConfig:
    db_path = overrides.get("db_path")
    mpv_path = overrides.get("mpv_path")
    seek_step_seconds = overrides.get("seek_step_seconds")
    speed_step = overrides.get("speed_step")
    speed_min = overrides.get("speed_min")
    speed_max = overrides.get("speed_max")

    return AppConfig(
        db_path=Path(db_path).expanduser() if db_path is not None else base.db_path,
        mpv_path=mpv_path if mpv_path is not None else base.mpv_path,
        seek_step_seconds=int(seek_step_seconds)
        if seek_step_seconds is not None
        else base.seek_step_seconds,
        speed_step=float(speed_step) if speed_step is not None else base.speed_step,
        speed_min=float(speed_min) if speed_min is not None else base.speed_min,
        speed_max=float(speed_max) if speed_max is not None else base.speed_max,
    )


def _load_toml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}

    with path.open("rb") as file:
        data = tomllib.load(file)

    if not isinstance(data, dict):
        return {}

    return data


def _load_env_overrides() -> dict[str, Any]:
    overrides: dict[str, Any] = {}

    if "VOXBOOK_DB_PATH" in os.environ:
        overrides["db_path"] = os.environ["VOXBOOK_DB_PATH"]

    if "VOXBOOK_MPV_PATH" in os.environ:
        overrides["mpv_path"] = os.environ["VOXBOOK_MPV_PATH"]

    if "VOXBOOK_SEEK_STEP_SECONDS" in os.environ:
        overrides["seek_step_seconds"] = os.environ["VOXBOOK_SEEK_STEP_SECONDS"]

    if "VOXBOOK_SPEED_STEP" in os.environ:
        overrides["speed_step"] = os.environ["VOXBOOK_SPEED_STEP"]

    if "VOXBOOK_SPEED_MIN" in os.environ:
        overrides["speed_min"] = os.environ["VOXBOOK_SPEED_MIN"]

    if "VOXBOOK_SPEED_MAX" in os.environ:
        overrides["speed_max"] = os.environ["VOXBOOK_SPEED_MAX"]

    return overrides


def load_config(path: Path | None = None) -> AppConfig:
    config = _default_config()

    if path is None:
        path = Path(_CONFIG_DIR_DEFAULT).expanduser() / _CONFIG_FILE_NAME

    file_overrides = _load_toml(path)
    config = _merge_config(config, file_overrides)

    env_overrides = _load_env_overrides()
    config = _merge_config(config, env_overrides)

    return config
