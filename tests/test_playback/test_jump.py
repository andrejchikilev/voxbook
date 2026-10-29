from unittest.mock import Mock

from voxbook.library.models import BookFile
from voxbook.playback.context import PlaybackContext
from voxbook.playback.player_actions import PlayerActions
from voxbook.playback.player_service import PlayerService


def make_file(index: int, duration: float) -> BookFile:
    return BookFile(path=f"file_{index}.mp3", index=index, duration=duration)


def test_jump_to_file_sets_context_target_and_triggers_jump_result() -> None:
    context = PlaybackContext()
    context.current_book_id = 1

    actions = PlayerActions(
        context=context,
        log=lambda _message: None,
        mpv=Mock(),
        status_renderer=Mock(),
    )

    actions.jump_to_file(3, 12.0)

    assert context.jump_target_index == 3
    assert context.jump_target_position == 12.0
    assert context.skip_to_next is True


def test_jump_to_position_sets_position_target() -> None:
    context = PlaybackContext()
    context.current_book_id = 1

    actions = PlayerActions(
        context=context,
        log=lambda _message: None,
        mpv=Mock(),
        status_renderer=Mock(),
    )

    actions.jump_to_position(123.0)

    assert context.jump_target_index is None
    assert context.jump_target_position == 123.0
    assert context.skip_to_next is True


def test_jump_to_bookmark_missing_returns_none() -> None:
    context = PlaybackContext()
    context.current_book_id = 1

    log_messages: list[str] = []
    actions = PlayerActions(
        context=context,
        log=log_messages.append,
        mpv=Mock(),
        status_renderer=Mock(),
    )

    actions.jump_to_bookmark(999)

    assert context.jump_target_index is None
    assert "Not found" in log_messages[0]


def test_jump_to_bookmark_wrong_book_logs_and_ignores() -> None:
    context = PlaybackContext()
    context.current_book_id = 1

    log_messages: list[str] = []
    actions = PlayerActions(
        context=context,
        log=log_messages.append,
        mpv=Mock(),
        status_renderer=Mock(),
    )

    actions.jump_to_bookmark(1)

    assert context.jump_target_index is None
    assert "belongs to book" in log_messages[0]


def test_player_service_jump_to_file_delegates_to_actions() -> None:
    context = PlaybackContext()
    context.current_book_id = 1

    actions = Mock(spec=PlayerActions)
    service = PlayerService(context=context, mpv=Mock(), playback_repository=Mock())
    service.actions = actions

    service.jump_to_file(5, 10.0)

    actions.jump_to_file.assert_called_once_with(5, 10.0)


def test_player_service_jump_to_position_delegates_to_actions() -> None:
    context = PlaybackContext()
    context.current_book_id = 1

    actions = Mock(spec=PlayerActions)
    service = PlayerService(context=context, mpv=Mock(), playback_repository=Mock())
    service.actions = actions

    service.jump_to_position(120.0)

    actions.jump_to_position.assert_called_once_with(120.0)


def test_player_service_jump_to_bookmark_delegates_to_actions() -> None:
    context = PlaybackContext()
    context.current_book_id = 1

    actions = Mock(spec=PlayerActions)
    service = PlayerService(context=context, mpv=Mock(), playback_repository=Mock())
    service.actions = actions

    service.jump_to_bookmark(7)

    actions.jump_to_bookmark.assert_called_once_with(7)
