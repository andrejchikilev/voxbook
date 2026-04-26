from pathlib import Path

from sqlmodel import SQLModel, create_engine

DB_PATH = Path.home() / ".local/share/voxbook/voxbook.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(f"sqlite:///{DB_PATH}")


def init_db() -> None:
    SQLModel.metadata.create_all(engine)
