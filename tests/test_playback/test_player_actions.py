from unittest.mock import Mock

from voxbook.playback.context import PlaybackContext
from voxbook.playback.player_actions import PlayerActions
from voxbook.playback.status_renderer import StatusRenderer


def _make_player_actions():
    context = PlaybackContext()
    mpv = Mock()
    renderer = Mock(spec=StatusRenderer)
    log = Mock()

    return PlayerActions(
        context=context,
        log=log,
        mpv=mpv,
        status_renderer=renderer,
    )


def test_volume_up_increases_volume_and_calls_mpv():
    actions = _make_player_actions()
    actions.context.playback_volume = 60.0
    player = Mock()
    actions.context.current_player = player

    actions.volume_up()

    assert actions.context.playback_volume == 65.0
    actions.mpv.set_volume.assert_called_once_with(player, 65.0)


def test_volume_down_decreases_volume_and_calls_mpv():
    actions = _make_player_actions()
    actions.context.playback_volume = 60.0
    player = Mock()
    actions.context.current_player = player

    actions.volume_down()

    assert actions.context.playback_volume == 55.0
    actions.mpv.set_volume.assert_called_once_with(player, 55.0)


def test_volume_up_clamps_to_maximum():
    actions = _make_player_actions()
    actions.context.playback_volume = 98.0
    player = Mock()
    actions.context.current_player = player

    actions.volume_up()

    assert actions.context.playback_volume == 100.0
    actions.mpv.set_volume.assert_called_once_with(player, 100.0)


def test_volume_down_clamps_to_minimum():
    actions = _make_player_actions()
    actions.context.playback_volume = 2.0
    player = Mock()
    actions.context.current_player = player

    actions.volume_down()

    assert actions.context.playback_volume == 0.0
    actions.mpv.set_volume.assert_called_once_with(player, 0.0)


def test_volume_up_without_player_updates_context_only():
    actions = _make_player_actions()
    actions.context.playback_volume = 60.0

    actions.volume_up()

    assert actions.context.playback_volume == 65.0
    actions.mpv.set_volume.assert_not_called()
