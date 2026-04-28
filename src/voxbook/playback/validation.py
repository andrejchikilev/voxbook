from pathlib import Path

from voxbook.playback.exceptions import AudioFileValidationError

SUPPORTED_AUDIO_EXTENSIONS = {".mp3", ".m4a", ".m4b", ".flac", ".ogg", ".opus"}

_VALID_AUDIO_FILES: set[Path] = set()
_INVALID_AUDIO_FILES: dict[Path, str] = {}


def clear_audio_validation_cache() -> None:
    _VALID_AUDIO_FILES.clear()
    _INVALID_AUDIO_FILES.clear()

def validate_audio_file(file_path: Path) -> None:
    resolved_path = file_path.resolve()

    if resolved_path in _VALID_AUDIO_FILES:
        return

    if resolved_path in _INVALID_AUDIO_FILES:
        raise AudioFileValidationError(_INVALID_AUDIO_FILES[resolved_path])

    try:
        _validate_audio_file_uncached(resolved_path)
    except AudioFileValidationError as error:
        _INVALID_AUDIO_FILES[resolved_path] = str(error)
        raise

    _VALID_AUDIO_FILES.add(resolved_path)


def _validate_audio_file_uncached(file_path: Path) -> None:
    if not file_path.exists():
        raise AudioFileValidationError("file does not exist")

    if not file_path.is_file():
        raise AudioFileValidationError("path is not a file")

    if file_path.suffix.lower() not in SUPPORTED_AUDIO_EXTENSIONS:
        raise AudioFileValidationError(f"unsupported extension: {file_path.suffix}")

    try:
        file_size = file_path.stat().st_size
    except OSError as error:
        raise AudioFileValidationError(f"cannot read file metadata: {error}") from error

    if file_size <= 0:
        raise AudioFileValidationError("file is empty")

    try:
        with file_path.open("rb") as audio_file:
            chunk = audio_file.read(1024)
    except OSError as error:
        raise AudioFileValidationError(f"file cannot be read: {error}") from error

    if not chunk:
        raise AudioFileValidationError("file cannot be partially read")
