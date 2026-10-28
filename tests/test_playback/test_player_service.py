from pathlib import Path
from unittest.mock import Mock

from voxbook.playback.player_service import PlayerService


def test_play_single_book_file_skips_invalid_file_without_starting_mpv(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "empty.mp3"
    file_path.write_bytes(b"")

    mpv = Mock()
    playback_repository = Mock()

    service = PlayerService(
        mpv=mpv,
        playback_repository=playback_repository,
    )

    # pylint: disable=protected-access
    result = service._play_single_book_file(
        book_id=1,
        file_index=1,
        file_path=file_path,
    )

    assert result == "next"
    mpv.create_player.assert_not_called()
    playback_repository.save_position.assert_called_once_with(
        1,
        2,
        0.0,
        speed=1.0,
    )


def test_get_volume_returns_none_when_no_player_is_active() -> None:
    service = PlayerService()

    assert service.get_volume() is None


def test_get_volume_passes_through_current_player_volume() -> None:
    player = Mock()
    mpv = Mock()
    mpv.get_volume.return_value = 80.0

    service = PlayerService(mpv=mpv)
    service.context.current_player = player

    assert service.get_volume() == 80.0
    mpv.get_volume.assert_called_once_with(player)


def test_set_volume_clamps_and_applies_to_current_player() -> None:
    player = Mock()
    mpv = Mock()

    service = PlayerService(mpv=mpv)
    service.context.current_player = player

    service.set_volume(120.0)
    service.set_volume(-10.0)
    service.set_volume(42.0)

    assert mpv.set_volume.call_args_list == [
        ((player, 100.0),),
        ((player, 0.0),),
        ((player, 42.0),),
    ]


def test_set_volume_does_nothing_when_no_player_is_active() -> None:
    mpv = Mock()
    service = PlayerService(mpv=mpv)

    service.set_volume(50.0)

    mpv.set_volume.assert_not_called()
