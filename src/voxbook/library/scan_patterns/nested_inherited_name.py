from pathlib import Path
import re
import unicodedata

from natsort import natsorted

from voxbook.library.scan_patterns.base import BasePattern, ScannedBook


class NestedInheritedNamePattern(BasePattern):
    name = "nested_inherited_name"

    def match(self, path: Path) -> list[ScannedBook]:
        if not path.is_dir():
            return []

        scanned_books: list[ScannedBook] = []

        for book_dir in self._find_matching_book_dirs(path):
            audio_files = natsorted(
                (
                    file
                    for file in book_dir.iterdir()
                    if self.is_audio_file(file)
                ),
                key=lambda p: p.name,
            )

            if not audio_files:
                continue

            scanned_books.append(
                ScannedBook(
                    title=book_dir.name,
                    path=book_dir,
                    files=audio_files,
                )
            )

        return scanned_books

    def _find_matching_book_dirs(self, root: Path) -> list[Path]:
        result: list[Path] = []

        for candidate in root.rglob("*"):
            if not candidate.is_dir():
                continue

            audio_files = [
                file
                for file in candidate.iterdir()
                if self.is_audio_file(file)
            ]

            if not audio_files:
                continue

            if self._matches_inherited_name(root, candidate, audio_files):
                result.append(candidate)

        return result

    def _matches_inherited_name(
        self,
        root: Path,
        book_dir: Path,
        audio_files: list[Path],
    ) -> bool:
        relative_parts = book_dir.relative_to(root).parts

        if not relative_parts:
            return False

        previous_name = root.name

        for current_name in relative_parts:
            if not _contains_normalized(current_name, previous_name):
                return False

            previous_name = current_name

        for file in audio_files:
            if not _contains_normalized(file.stem, book_dir.name):
                return False

        return True


def _normalize(value: str) -> str:
    value = unicodedata.normalize("NFC", value)
    value = value.lower()
    value = value.replace("ё", "е")
    value = re.sub(r"[_\-.–—]+", " ", value)
    value = re.sub(r"[()\[\]{}]", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def _contains_normalized(value: str, expected_part: str) -> bool:
    return _normalize(expected_part) in _normalize(value)