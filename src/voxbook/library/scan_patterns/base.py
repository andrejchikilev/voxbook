from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class ScannedBook:
    title: str
    path: Path
    files: list[Path]


class ScanPattern(Protocol):
    name: str

    def match(self, path: Path) -> list[ScannedBook]:
        ...


class BasePattern:
    AUDIO_EXTS = {".mp3", ".m4a", ".m4b", ".flac", ".ogg", ".opus"}

    def is_audio_file(self, path: Path) -> bool:
        return path.is_file() and path.suffix.lower() in self.AUDIO_EXTS