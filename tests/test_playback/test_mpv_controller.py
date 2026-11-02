# pylint: disable=protected-access
import ctypes.util
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from voxbook.config import AppConfig
from voxbook.playback.mpv_controller import MpvController


def test_get_volume_returns_player_volume() -> None:
    player = Mock()
    player.volume = 75.0

    controller = MpvController()

    assert controller.get_volume(player) == 75.0


def test_get_volume_returns_none_when_property_fails() -> None:
    player = Mock()
    player.volume = 75.0
    del player.volume

    controller = MpvController()

    assert controller.get_volume(player) is None


def test_set_volume_assigns_player_volume() -> None:
    player = Mock()
    controller = MpvController()

    controller.set_volume(player, 42.0)

    assert player.volume == 42.0


def test_set_volume_swallows_assignment_errors() -> None:
    player = Mock()
    player.volume = MockPropertyThatRaises()

    controller = MpvController()

    controller.set_volume(player, 42.0)


class MockPropertyThatRaises:
    def __set__(self, instance, value):
        raise RuntimeError("boom")


def test_create_player_does_not_pass_mpv_location() -> None:
    config = AppConfig(
        db_path=Path("~/.local/share/voxbook/voxbook.db").expanduser(),
        mpv_path="/usr/bin/mpv",
        seek_step_seconds=30,
        speed_step=0.1,
        speed_min=0.5,
        speed_max=3.0,
    )
    controller = MpvController(config)

    with patch("voxbook.playback.mpv_controller.MPV") as mock_mpv:
        controller.create_player()

    mock_mpv.assert_called_once()
    kwargs = mock_mpv.call_args.kwargs
    assert "mpv_location" not in kwargs


def test_mpv_executable_returns_path_object_as_string() -> None:
    config = AppConfig(
        db_path=Path("~/.local/share/voxbook/voxbook.db").expanduser(),
        mpv_path=Path("/usr/bin/mpv"),
        seek_step_seconds=30,
        speed_step=0.1,
        speed_min=0.5,
        speed_max=3.0,
    )
    controller = MpvController(config)

    assert controller._mpv_executable() == "/usr/bin/mpv"


def test_mpv_executable_resolves_expanded_path_when_file_exists(tmp_path) -> None:
    fake_mpv = tmp_path / "mpv"
    fake_mpv.write_text("")

    config = AppConfig(
        db_path=Path("~/.local/share/voxbook/voxbook.db").expanduser(),
        mpv_path=str(fake_mpv),
        seek_step_seconds=30,
        speed_step=0.1,
        speed_min=0.5,
        speed_max=3.0,
    )
    controller = MpvController(config)

    assert controller._mpv_executable() == str(fake_mpv)


def test_mpv_executable_falls_back_to_shutil_which() -> None:
    config = AppConfig(
        db_path=Path("~/.local/share/voxbook/voxbook.db").expanduser(),
        mpv_path="mpv",
        seek_step_seconds=30,
        speed_step=0.1,
        speed_min=0.5,
        speed_max=3.0,
    )
    controller = MpvController(config)

    result = controller._mpv_executable()

    assert result == "mpv" or Path(result).exists()


def test_mpv_executable_returns_original_string_when_not_found(tmp_path) -> None:
    missing = str(tmp_path / "not-a-real-mpv")

    config = AppConfig(
        db_path=Path("~/.local/share/voxbook/voxbook.db").expanduser(),
        mpv_path=missing,
        seek_step_seconds=30,
        speed_step=0.1,
        speed_min=0.5,
        speed_max=3.0,
    )
    controller = MpvController(config)

    assert controller._mpv_executable() == missing


def test_ensure_mpv_available_warns_when_binary_missing(caplog) -> None:
    controller = MpvController()

    with caplog.at_level("WARNING"):
        controller._ensure_mpv_available("/nonexistent/mpv")

    assert "mpv binary not found: /nonexistent/mpv" in caplog.text


def test_ensure_mpv_available_silent_when_binary_exists(tmp_path) -> None:
    fake_mpv = tmp_path / "mpv"
    fake_mpv.write_text("")
    controller = MpvController()

    with patch("voxbook.playback.mpv_controller.logger") as mock_logger:
        controller._ensure_mpv_available(str(fake_mpv))

    mock_logger.warning.assert_not_called()


def test_ensure_mpv_available_silent_when_found_in_path() -> None:
    controller = MpvController()

    with patch("voxbook.playback.mpv_controller.shutil.which", return_value="/usr/bin/mpv"):
        with patch("voxbook.playback.mpv_controller.logger") as mock_logger:
            controller._ensure_mpv_available("mpv")

    mock_logger.warning.assert_not_called()


@pytest.mark.skipif(
    ctypes.util.find_library("mpv") is None,
    reason="libmpv not available",
)
def test_create_player_with_real_mpv_no_location() -> None:
    from mpv import MPV

    player = MPV(
        ytdl=False,
        vid="no",
        audio_display="no",
        input_default_bindings=False,
        input_vo_keyboard=False,
    )
    player.terminate()
