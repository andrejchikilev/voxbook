from unittest.mock import Mock

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
