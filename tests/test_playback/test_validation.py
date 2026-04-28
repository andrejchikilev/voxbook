from pathlib import Path

import pytest

from voxbook.playback.exceptions import AudioFileValidationError
from voxbook.playback.validation import clear_audio_validation_cache, validate_audio_file


def test_validate_audio_file_ok(tmp_path: Path) -> None:
    clear_audio_validation_cache()
    file_path = tmp_path / "book.mp3"
    file_path.write_bytes(b"fake audio content")

    validate_audio_file(file_path)


def test_validate_audio_file_missing(tmp_path: Path) -> None:
    clear_audio_validation_cache()
    file_path = tmp_path / "missing.mp3"

    with pytest.raises(AudioFileValidationError, match="file does not exist"):
        validate_audio_file(file_path)


def test_validate_audio_file_directory(tmp_path: Path) -> None:
    clear_audio_validation_cache()
    with pytest.raises(AudioFileValidationError, match="path is not a file"):
        validate_audio_file(tmp_path)


def test_validate_audio_file_unsupported_extension(tmp_path: Path) -> None:
    clear_audio_validation_cache()
    file_path = tmp_path / "book.txt"
    file_path.write_bytes(b"content")

    with pytest.raises(AudioFileValidationError, match="unsupported extension"):
        validate_audio_file(file_path)


def test_validate_audio_file_empty(tmp_path: Path) -> None:
    clear_audio_validation_cache()
    file_path = tmp_path / "book.mp3"
    file_path.write_bytes(b"")

    with pytest.raises(AudioFileValidationError, match="file is empty"):
        validate_audio_file(file_path)
