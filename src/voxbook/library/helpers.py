from pathlib import Path

from mutagen import File as MutagenFile


def get_audio_duration(path: Path) -> float:
    audio = MutagenFile(path)
    if audio is None or audio.info is None:
        return 0.0

    return float(audio.info.length or 0.0)
