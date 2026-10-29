"""Tests for player actions."""
from pathlib import Path
from unittest.mock import Mock

from voxbook.config import AppConfig
from voxbook.playback.context import PlaybackContext
from voxbook.playback.mpv_controller import MpvController
from voxbook.playback.player_actions import PlayerActions
from voxbook.playback.status_renderer import StatusRenderer


def _make_actions(
    config: AppConfig | None = None,
) -> tuple[PlayerActions, Mock, Mock, PlaybackContext]:
    context = PlaybackContext()
    mpv = Mock(spec=MpvController)
    status_renderer = Mock(spec=StatusRenderer)
    actions = PlayerActions(
        context=context,
        log=Mock(),
        mpv=mpv,
        status_renderer=status_renderer,
        config=config,
    )
    return actions, mpv, status_renderer, context


def test_seek_forward_uses_config_step() -> None:
    """Test seek forward uses configured step value."""
    config = AppConfig(
        db_path=Path("/tmp/db"),
        mpv_path="mpv",
        seek_step_seconds=60,
        speed_step=0.1,
        speed_min=0.5,
        speed_max=3.0,
    )
    actions, mpv, _, _ = _make_actions(config)
    context = actions.context
    context.current_player = Mock()

    actions.seek_forward()

    mpv.seek.assert_called_once_with(context.current_player, 60, reference="relative")


def test_seek_backward_uses_config_step() -> None:
    """Test seek backward uses configured step value."""
    config = AppConfig(
        db_path=Path("/tmp/db"),
        mpv_path="mpv",
        seek_step_seconds=45,
        speed_step=0.1,
        speed_min=0.5,
        speed_max=3.0,
    )
    actions, mpv, _, _ = _make_actions(config)
    context = actions.context
    context.current_player = Mock()

    actions.seek_backward()

    mpv.seek.assert_called_once_with(context.current_player, -45, reference="relative")


def test_speed_up_respects_config_max_and_step() -> None:
    """Test speed up uses configured max and step."""
    config = AppConfig(
        db_path=Path("/tmp/db"),
        mpv_path="mpv",
        seek_step_seconds=30,
        speed_step=0.5,
        speed_min=0.5,
        speed_max=2.0,
    )
    actions, mpv, _, context = _make_actions(config)
    context.current_player = Mock()
    context.playback_speed = 1.0

    actions.speed_up()

    assert context.playback_speed == 1.5
    mpv.set_speed.assert_called_once_with(context.current_player, 1.5)


def test_speed_down_respects_config_min_and_step() -> None:
    """Test speed down uses configured min and step."""
    config = AppConfig(
        db_path=Path("/tmp/db"),
        mpv_path="mpv",
        seek_step_seconds=30,
        speed_step=0.5,
        speed_min=1.0,
        speed_max=3.0,
    )
    actions, mpv, _, context = _make_actions(config)
    context.current_player = Mock()
    context.playback_speed = 1.5

    actions.speed_down()

    assert context.playback_speed == 1.0
    mpv.set_speed.assert_called_once_with(context.current_player, 1.0)
