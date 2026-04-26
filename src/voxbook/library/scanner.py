from pathlib import Path

from natsort import natsorted
from sqlmodel import Session, select

from voxbook.library.helpers import get_audio_duration
from voxbook.library.models import Book, BookFile
from voxbook.library.scan_patterns.base import ScannedBook, ScanPattern
from voxbook.library.scan_patterns.book_folder_with_parts import BookFolderWithPartsPattern
from voxbook.library.scan_patterns.flat_book_folder import FlatBookFolderPattern
from voxbook.library.scan_patterns.nested_inherited_name import NestedInheritedNamePattern
from voxbook.library.scan_patterns.single_file import SingleFilePattern
from voxbook.storage.db import engine


def scan_library(library_root: Path) -> None:
    library_root = library_root.expanduser().resolve()

    if not library_root.exists():
        raise FileNotFoundError(f"Library path does not exist: {library_root}")

    patterns: list[ScanPattern] = [
        BookFolderWithPartsPattern(),
        NestedInheritedNamePattern(),
        FlatBookFolderPattern(),
        SingleFilePattern(),
    ]

    with Session(engine) as session:
        for entry in natsorted(library_root.iterdir(), key=lambda p: p.name):
            scanned_books = match_books(entry, patterns)

            for scanned_book in scanned_books:
                save_scanned_book(session, scanned_book)

        session.commit()


def match_books(path: Path, patterns: list[ScanPattern]) -> list[ScannedBook]:
    for pattern in patterns:
        scanned_books = pattern.match(path)

        if scanned_books:
            return scanned_books

    return []


def save_scanned_book(session: Session, scanned_book: ScannedBook) -> None:
    book = session.exec(select(Book).where(Book.path == str(scanned_book.path))).first()

    if book is None:
        book = Book(
            title=scanned_book.title,
            path=str(scanned_book.path),
        )
        session.add(book)
        session.commit()
        session.refresh(book)

    assert book.id is not None

    current_paths = {str(file) for file in scanned_book.files}

    for index, file in enumerate(scanned_book.files, start=1):
        existing_file = session.exec(select(BookFile).where(BookFile.path == str(file))).first()

        if existing_file is None:
            session.add(
                BookFile(
                    book_id=book.id,
                    path=str(file),
                    index=index,
                    duration=get_audio_duration(file),
                )
            )
        else:
            existing_file.book_id = book.id
            existing_file.index = index
            existing_file.duration = get_audio_duration(file)

    cleanup_missing_book_files(
        session=session,
        book_id=book.id,
        current_paths=current_paths,
    )


def cleanup_missing_book_files(
    session: Session,
    book_id: int,
    current_paths: set[str],
) -> None:
    existing_files = session.exec(select(BookFile).where(BookFile.book_id == book_id)).all()

    for existing_file in existing_files:
        if existing_file.path not in current_paths:
            session.delete(existing_file)
