from typing import Protocol


class _HasDurationAndIndex(Protocol):
    duration: float
    index: int


def format_seconds(seconds: float) -> str:
    total_seconds = int(seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60

    if hours:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    return f"{minutes:02d}:{secs:02d}"


def parse_timestamp(timestamp: str) -> float:
    parts = timestamp.strip().split(":")

    if len(parts) == 1:
        return float(parts[0])

    if len(parts) == 2:
        minutes, seconds = parts
        return float(minutes) * 60 + float(seconds)

    if len(parts) == 3:
        hours, minutes, seconds = parts
        return float(hours) * 3600 + float(minutes) * 60 + float(seconds)

    raise ValueError(f"Invalid timestamp format: {timestamp}")


def book_position_to_file_position(
    files: list[_HasDurationAndIndex],
    book_position: float,
) -> tuple[int, float]:
    if not files:
        return (1, 0.0)

    elapsed = 0.0

    for book_file in files:
        file_start = elapsed
        file_end = elapsed + book_file.duration

        if book_position < file_end:
            position_in_file = max(0.0, book_position - file_start)
            return (book_file.index, position_in_file)

        elapsed = file_end

    last_file = files[-1]
    return (last_file.index, last_file.duration)
