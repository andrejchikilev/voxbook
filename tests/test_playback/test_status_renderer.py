from io import StringIO
from unittest.mock import Mock

import pytest
from rich.cells import cell_len
from rich.console import Console

from voxbook.playback.status_renderer import StatusRenderer


def test_render_status_line_clears_previous_output_and_truncates_to_terminal_width(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = StringIO()
    console = Console(file=output, force_terminal=True)
    mpv = Mock()
    mpv.get_position.return_value = 12.0
    renderer = StatusRenderer(log=Mock(), mpv=mpv, console=console)
    monkeypatch.setenv("COLUMNS", "28")

    renderer.render_status_line(
        player=Mock(),
        book_title="Аудиокнига — очень длинное название 🎧",
        file_index=1,
        speed=1.0,
    )

    rendered = output.getvalue()
    status = rendered.split("\x1b[2K", maxsplit=1)[1]
    assert rendered.startswith("\r")
    assert cell_len(status) <= 27
    assert status.endswith("…")


def test_render_status_line_uses_updated_width_after_terminal_resize(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = StringIO()
    console = Console(file=output, force_terminal=True)
    mpv = Mock()
    mpv.get_position.return_value = 12.0
    renderer = StatusRenderer(log=Mock(), mpv=mpv, console=console)
    title = "A long audiobook title that fits after resizing"

    monkeypatch.setenv("COLUMNS", "20")
    renderer.render_status_line(player=Mock(), book_title=title, file_index=1, speed=1.0)

    monkeypatch.setenv("COLUMNS", "100")
    renderer.render_status_line(player=Mock(), book_title=title, file_index=1, speed=1.0)

    parts = output.getvalue().split("\r\x1b[2K")
    assert len(parts) == 3
    first, second = parts[1:]
    assert "…" in first
    assert title in second
