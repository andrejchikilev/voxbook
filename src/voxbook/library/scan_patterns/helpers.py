
from pathlib import Path

from voxbook.library.scan_patterns.base import ScannedBook

def create_scanned_book(path: Path, audio_files: list[Path]) -> list[ScannedBook]:
    if not audio_files:
        return []
    return [ScannedBook(title=path.name, path=path, files=audio_files)]