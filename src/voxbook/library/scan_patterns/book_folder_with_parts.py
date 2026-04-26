from pathlib import Path

from natsort import natsorted

from voxbook.library.scan_patterns.base import ScannedBook

AUDIO_EXTS = {".mp3", ".m4a", ".m4b", ".flac", ".ogg", ".opus"}


class BookFolderWithPartsPattern:
    name = "book_folder_with_parts"

    def match(self, path: Path) -> list[ScannedBook]:
        if not path.is_dir():
            return []

        part_dirs = [
            child
            for child in path.iterdir()
            if child.is_dir() and _looks_like_part_dir(child.name)
        ]

        if not part_dirs:
            return []

        audio_files: list[Path] = []

        for part_dir in natsorted(part_dirs, key=lambda p: p.name):
            files = natsorted(
                (
                    file
                    for file in part_dir.rglob("*")
                    if file.is_file() and file.suffix.lower() in AUDIO_EXTS
                ),
                key=lambda p: str(p.relative_to(path)),
            )
            audio_files.extend(files)

        if not audio_files:
            return []

        return [ScannedBook(
            title=path.name,
            path=path,
            files=audio_files,
        )]


def _looks_like_part_dir(name: str) -> bool:
    normalized = name.lower().replace(" ", "").replace("_", "").replace("-", "")

    if normalized.isdigit():
        return True

    prefixes = ("cd", "disc", "disk", "part", "часть")
    return any(normalized.startswith(prefix) for prefix in prefixes)