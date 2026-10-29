from pathlib import Path

from sqlmodel import SQLModel, create_engine

from voxbook.config import load_config


def _current_db_path() -> Path:
    return load_config().db_path


_DB_PATH = _current_db_path()
_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(f"sqlite:///{_DB_PATH}")


def __getattr__(name: str) -> Path:
    if name == "DB_PATH":
        return _current_db_path()

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def get_db_path() -> Path:
    return _current_db_path()


def init_db() -> None:
    SQLModel.metadata.create_all(engine)
