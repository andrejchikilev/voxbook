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
