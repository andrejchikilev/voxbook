from unittest.mock import Mock, patch

from voxbook.playback.models import BookPlaybackState
from voxbook.playback.repository import PlaybackRepository


def test_save_and_load_position_round_trip_persists_volume():
    repository = PlaybackRepository()

    captured = {"state": None}

    def fake_add(state):
        captured["state"] = state

    mock_session = Mock()
    mock_session.get.return_value = None
    mock_session.add.side_effect = fake_add

    with patch("voxbook.playback.repository.Session") as mock_session_class:
        mock_session_class.return_value.__enter__ = Mock(return_value=mock_session)
        mock_session_class.return_value.__exit__ = Mock(return_value=False)

        repository.save_position(
            book_id=1,
            file_index=2,
            position=120.0,
            speed=1.5,
            volume=75.0,
        )

    created = captured["state"]
    assert isinstance(created, BookPlaybackState)
    assert created.volume == 75.0

    mock_session.get.return_value = created

    with patch("voxbook.playback.repository.Session") as mock_session_class:
        mock_session_class.return_value.__enter__ = Mock(return_value=mock_session)
        mock_session_class.return_value.__exit__ = Mock(return_value=False)

        loaded = repository.load_position(1)

    assert loaded is not None
    assert loaded.volume == 75.0
