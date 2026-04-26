from pathlib import Path

from natsort import natsorted

from voxbook.library.scan_patterns.base import ScannedBook
from voxbook.library.scan_patterns.helpers import create_scanned_book

AUDIO_EXTS = {".mp3", ".m4a", ".m4b", ".flac", ".ogg", ".opus"}


class FlatBookFolderPattern:
    name = "flat_book_folder"

    def match(self, path: Path) -> list[ScannedBook]:
        if not path.is_dir():
            return []

        audio_files = natsorted(
            (
                file
                for file in path.iterdir()
                if file.is_file() and file.suffix.lower() in AUDIO_EXTS
            ),
            key=lambda p: p.name,
        )

        return create_scanned_book(path, audio_files)
