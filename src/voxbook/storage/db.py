from pathlib import Path

from sqlalchemy import Engine, text
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


def _ensure_columns(db_engine: Engine) -> None:
    """Add columns declared in models that are missing from existing tables."""
    # Column types matter for SQLite schema drift: TEXT for strings, REAL for floats.
    expected: dict[str, dict[str, str]] = {
        "book": {"author": "TEXT", "series": "TEXT", "narrator": "TEXT"},
        "bookplaybackstate": {"volume": "REAL"},
    }

    with db_engine.connect() as connection:
        for table_name, columns in expected.items():
            existing = {
                row[1]
                for row in connection.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
            }

            for column, column_type in columns.items():
                if column in existing:
                    continue

                connection.execute(
                    text(f"ALTER TABLE {table_name} ADD COLUMN {column} {column_type}")
                )

        connection.commit()


def init_db() -> None:
    SQLModel.metadata.create_all(engine)
    _ensure_columns(engine)
