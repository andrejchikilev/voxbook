from unittest.mock import patch

from sqlmodel import Session
from typer.testing import CliRunner

from voxbook.cli import app
from voxbook.library.models import Book, BookFile
from voxbook.storage.db import engine

runner = CliRunner()


def test_goto_missing_book() -> None:
    result = runner.invoke(app, ["goto", "9999", "1:23"])

    assert result.exit_code == 1
    assert "Book not found" in result.output


def test_goto_no_files(tmp_path) -> None:
    with Session(engine) as session:
        book = Book(title="empty book", path=str(tmp_path / "empty-book"))
        session.add(book)
        session.commit()
        session.refresh(book)
        book_id = book.id

    result = runner.invoke(app, ["goto", str(book_id), "1:23"])

    assert result.exit_code == 1
    assert "Book has no files" in result.output


def test_goto_parses_mm_ss_and_starts_play(tmp_path) -> None:
    with Session(engine) as session:
        book = Book(title="goto book", path=str(tmp_path))
        session.add(book)
        session.commit()
        session.refresh(book)
        book_id = book.id

        file1 = BookFile(book_id=book_id, path=str(tmp_path / "01.mp3"), index=1, duration=100)
        file2 = BookFile(book_id=book_id, path=str(tmp_path / "02.mp3"), index=2, duration=100)
        session.add(file1)
        session.add(file2)
        session.commit()

    with patch("voxbook.cli.play") as mock_play:
        result = runner.invoke(app, ["goto", str(book_id), "1:23"])

    assert result.exit_code == 0, result.output
    assert "Goto: 01:23 (file 1, pos 01:23)" in result.output
    mock_play.assert_called_once_with(book_id)


def test_goto_parses_hh_mm_ss(tmp_path) -> None:
    with Session(engine) as session:
        book = Book(title="goto book 2", path=str(tmp_path))
        session.add(book)
        session.commit()
        session.refresh(book)
        book_id = book.id

        file1 = BookFile(book_id=book_id, path=str(tmp_path / "01.mp3"), index=1, duration=3600)
        file2 = BookFile(book_id=book_id, path=str(tmp_path / "02.mp3"), index=2, duration=3600)
        session.add(file1)
        session.add(file2)
        session.commit()

    with patch("voxbook.cli.play") as mock_play:
        result = runner.invoke(app, ["goto", str(book_id), "1:23:45"])

    assert result.exit_code == 0, result.output
    assert "Goto: 01:23:45 (file 2, pos 23:45)" in result.output
    mock_play.assert_called_once_with(book_id)


def test_goto_invalid_timestamp(tmp_path) -> None:
    with Session(engine) as session:
        book = Book(title="goto bad", path=str(tmp_path))
        session.add(book)
        session.commit()
        session.refresh(book)
        book_id = book.id

        file1 = BookFile(book_id=book_id, path=str(tmp_path / "01.mp3"), index=1, duration=100)
        session.add(file1)
        session.commit()

    result = runner.invoke(app, ["goto", str(book_id), "abc"])

    assert result.exit_code == 1
    assert "Invalid position" in result.output
