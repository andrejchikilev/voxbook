from voxbook.helpers import book_position_to_file_position, parse_timestamp
from voxbook.library.models import BookFile


def make_file(index: int, duration: float) -> BookFile:
    return BookFile(path=f"file_{index}.mp3", index=index, duration=duration)


def test_book_position_to_file_position_start() -> None:
    files = [make_file(1, 100), make_file(2, 100)]
    assert book_position_to_file_position(files, 0.0) == (1, 0.0)


def test_book_position_to_file_position_inside_first_file() -> None:
    files = [make_file(1, 100), make_file(2, 100)]
    assert book_position_to_file_position(files, 30.0) == (1, 30.0)


def test_book_position_to_file_position_at_file_boundary() -> None:
    files = [make_file(1, 100), make_file(2, 100)]
    assert book_position_to_file_position(files, 100.0) == (1, 100.0)


def test_book_position_to_file_position_inside_second_file() -> None:
    files = [make_file(1, 100), make_file(2, 100)]
    assert book_position_to_file_position(files, 150.0) == (2, 50.0)


def test_book_position_to_file_position_end() -> None:
    files = [make_file(1, 100), make_file(2, 100)]
    assert book_position_to_file_position(files, 200.0) == (2, 100.0)


def test_book_position_to_file_position_past_end_clamps() -> None:
    files = [make_file(1, 100), make_file(2, 100)]
    assert book_position_to_file_position(files, 300.0) == (2, 100.0)


def test_book_position_to_file_position_negative_clamps_to_start() -> None:
    files = [make_file(1, 100), make_file(2, 100)]
    assert book_position_to_file_position(files, -10.0) == (1, 0.0)


def test_book_position_to_file_position_empty_files() -> None:
    assert book_position_to_file_position([], 10.0) == (1, 0.0)


def test_parse_timestamp_mm_ss() -> None:
    assert parse_timestamp("1:23") == 83.0


def test_parse_timestamp_hh_mm_ss() -> None:
    assert parse_timestamp("1:23:45") == 5025.0


def test_parse_timestamp_seconds_only() -> None:
    assert parse_timestamp("45") == 45.0


def test_parse_timestamp_with_whitespace() -> None:
    assert parse_timestamp("  1:23  ") == 83.0
