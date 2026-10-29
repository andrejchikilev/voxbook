"""Tests for library root tracking and rescan."""
from pathlib import Path

import pytest
from sqlmodel import Session, create_engine, select

from voxbook.library.models import Book, BookFile, LibraryRoot
from voxbook.library.scanner import rescan_libraries, save_library_root, scan_library
from voxbook.storage import db as db_module
from voxbook.storage.db import init_db


def _make_audio_file(path: Path) -> None:
    """Create a tiny valid MP3 file at path."""
    path.write_bytes(
        bytes.fromhex(
            "49443303000000000010474F0001000000000000000000000000000000000000"
            "0000FFFB90000000000000000000000000000000000000000000000000000000"
        )
    )


@pytest.fixture(autouse=True)
def _isolated_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Use a fresh file-based database for every test."""
    db_path = tmp_path / "voxbook.db"
    test_engine = create_engine(f"sqlite:///{db_path}")

    monkeypatch.setattr("voxbook.storage.db.DB_PATH", db_path)
    db_module.DB_PATH = db_path
    monkeypatch.setattr("voxbook.storage.db.engine", test_engine)
    db_module.engine = test_engine
    monkeypatch.setattr("voxbook.library.scanner.engine", test_engine)

    init_db()
    yield


def test_save_library_root_upserts_without_duplicates(tmp_path: Path):
    root = tmp_path / "Audiobooks"
    root.mkdir()

    with Session(db_module.engine) as session:
        save_library_root(session, root)
        save_library_root(session, root)
        session.commit()

    with Session(db_module.engine) as session:
        roots = session.exec(select(LibraryRoot)).all()

    assert len(roots) == 1
    assert roots[0].path == str(root.resolve())


def test_scan_remembers_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    root = tmp_path / "Audiobooks"
    root.mkdir()

    book_folder = root / "Test Book"
    book_folder.mkdir()
    audio_file = book_folder / "chapter1.mp3"
    _make_audio_file(audio_file)

    monkeypatch.setattr(
        "voxbook.library.scanner.get_audio_duration",
        lambda path: 60.0,
    )

    scan_library(root)

    with Session(db_module.engine) as session:
        roots = session.exec(select(LibraryRoot)).all()
        books = session.exec(select(Book)).all()

    assert len(roots) == 1
    assert roots[0].path == str(root.resolve())
    assert len(books) == 1
    assert books[0].title == "Test Book"


def test_rescan_without_roots_warns():
    roots = rescan_libraries()

    assert roots == []


def test_rescan_with_two_roots(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    root_a = tmp_path / "A"
    root_a.mkdir()
    root_b = tmp_path / "B"
    root_b.mkdir()

    for name, root in [("Alpha", root_a), ("Beta", root_b)]:
        book_folder = root / name
        book_folder.mkdir()
        audio_file = book_folder / "part1.mp3"
        _make_audio_file(audio_file)

    monkeypatch.setattr(
        "voxbook.library.scanner.get_audio_duration",
        lambda path: 60.0,
    )

    scan_library(root_a)
    scan_library(root_b)

    with Session(db_module.engine) as session:
        books = session.exec(select(Book)).all()
        assert len(books) == 2

    # Remove Beta from disk so rescan picks up only Alpha again
    for child in root_b.iterdir():
        for file in child.iterdir():
            file.unlink()
        child.rmdir()
    root_b.rmdir()

    rescan_libraries()

    with Session(db_module.engine) as session:
        roots = session.exec(select(LibraryRoot)).all()
        books = session.exec(select(Book)).all()
        files = session.exec(select(BookFile)).all()

    assert len(roots) == 2
    assert len(books) == 2
    assert len(files) == 2


def test_roots_list_and_remove(tmp_path: Path):
    root_a = tmp_path / "A"
    root_a.mkdir()
    root_b = tmp_path / "B"
    root_b.mkdir()

    with Session(db_module.engine) as session:
        session.add(LibraryRoot(path=str(root_a.resolve())))
        session.add(LibraryRoot(path=str(root_b.resolve())))
        session.commit()

    with Session(db_module.engine) as session:
        items = session.exec(select(LibraryRoot).order_by(LibraryRoot.added_at)).all()
        assert len(items) == 2

        remaining = session.exec(
            select(LibraryRoot).where(LibraryRoot.path == str(root_a.resolve()))
        ).first()
        session.delete(remaining)
        session.commit()

    with Session(db_module.engine) as session:
        remaining = session.exec(select(LibraryRoot)).all()

    assert len(remaining) == 1
    assert remaining[0].path == str(root_b.resolve())
