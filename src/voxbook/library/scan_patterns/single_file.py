from pathlib import Path

from voxbook.library.scan_patterns.base import ScannedBook

AUDIO_EXTS = {".mp3", ".m4a", ".m4b", ".flac", ".ogg", ".opus"}


class SingleFilePattern:
    name = "single_file"

    def match(self, path: Path) -> list[ScannedBook]:
        if not path.is_file():
            return []

        if path.suffix.lower() not in AUDIO_EXTS:
            return []

        return [
            ScannedBook(
                title=path.stem,
                path=path,
                files=[path],
            )
        ]
