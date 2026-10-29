from pathlib import Path

from sqlalchemy import Engine, text
from sqlmodel import SQLModel, create_engine

DB_PATH = Path.home() / ".local/share/voxbook/voxbook.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(f"sqlite:///{DB_PATH}")


def _ensure_columns(db_engine: Engine) -> None:
    """Add any columns declared in models that are missing from existing tables."""
    expected = {
        "book": {"author", "series", "narrator"},
    }

    with db_engine.connect() as connection:
        for table_name, columns in expected.items():
            existing = {
                row[1]
                for row in connection.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
            }

            for column in columns - existing:
                connection.execute(
                    text(f"ALTER TABLE {table_name} ADD COLUMN {column} TEXT")
                )

        connection.commit()


def init_db() -> None:
    SQLModel.metadata.create_all(engine)
    _ensure_columns(engine)
