from pathlib import Path
from typing import Literal

import typer
from rich.console import Console
from rich.markup import escape
from rich.table import Table
from sqlmodel import Session, select

from voxbook.helpers import format_seconds
from voxbook.library.models import Book, BookFile
from voxbook.library.progress import book_progress, book_updated_at
from voxbook.library.repository import delete_bookmark, get_bookmark, list_bookmarks
from voxbook.library.scanner import scan_library
from voxbook.playback.player_service import PlayerService
from voxbook.playback.repository import PlaybackRepository
from voxbook.storage.db import DB_PATH, engine, init_db

app = typer.Typer()
console = Console()
playback_repository = PlaybackRepository()

FilterStatus = Literal["not-started", "in-progress", "finished"]
SortKey = Literal["title", "progress", "recent"]


@app.callback()
def main() -> None:
    init_db()


@app.command()
def play(book_id: int) -> None:
    with Session(engine) as session:
        book = session.get(Book, book_id)

        if book is None:
            console.print("[red]Book not found[/red]")
            raise typer.Exit(code=1)

        files = session.exec(
            select(BookFile).where(BookFile.book_id == book_id).order_by(BookFile.index)
        ).all()

    if not files:
        console.print("[red]Book has no files[/red]")
        raise typer.Exit(code=1)

    console.print(f"[green]Playing:[/green] {escape(book.title)}")
    console.print(
        "[dim]space: pause/play | ←/→: seek | n/p: next/prev file | "
        "</>: speed | =: normal speed | s: status | b: bookmark | q: quit[/dim]"
    )

    player_service = PlayerService(
        log=lambda message: console.print(escape(message)),
    )
    player_service.play_book(book_id, list(files), book.title)


@app.command()
def resume() -> None:
    state = playback_repository.load_last_position()

    if state is None:
        console.print("[yellow]Nothing to resume[/yellow]")
        raise typer.Exit()

    play(state.book_id)


@app.command()
def scan(path: Path) -> None:
    scan_library(path)
    console.print(f"Scanned directory: {escape(str(path))}")


@app.command()
def search(query: str) -> None:
    with Session(engine) as session:
        books = session.exec(
            select(Book).where(Book.title.ilike(f"%{query}%")).order_by(Book.title)
        ).all()

    if not books:
        console.print("[yellow]Nothing found[/yellow]")
        return

    for book in books:
        console.print(f"{book.id}: {escape(book.title)}")


def _load_book_summary(session: Session, book: Book) -> dict:
    book_files = session.exec(
        select(BookFile).where(BookFile.book_id == book.id).order_by(BookFile.index)
    ).all()
    book_id = book.id
    assert book_id is not None
    state = playback_repository.load_position(book_id)
    book_status, position, total = book_progress(list(book_files), state)
    return {
        "state": state,
        "status": book_status,
        "position": position,
        "total": total,
    }


def _sort_books(books: list[Book], sort: SortKey, summaries: dict) -> None:
    if sort == "title":
        books.sort(key=lambda book: book.title)
    elif sort == "progress":
        books.sort(
            key=lambda book: (
                summaries[book.id]["position"] / summaries[book.id]["total"]
                if summaries[book.id]["total"] > 0
                else 0.0
            ),
            reverse=True,
        )
    elif sort == "recent":
        books.sort(
            key=lambda book: book_updated_at(summaries[book.id]["state"]),
            reverse=True,
        )


@app.command("list")
def list_books(
    filter_status: FilterStatus | None = typer.Option(
        None, "--filter", "-f", help="Filter by status: not-started, in-progress, finished"
    ),
    sort: SortKey = typer.Option("title", "--sort", "-s", help="Sort by: title, progress, recent"),
) -> None:
    with Session(engine) as session:
        books = list(session.exec(select(Book)).all())
        summaries = {book.id: _load_book_summary(session, book) for book in books}

        if filter_status:
            target = filter_status.replace("-", " ")
            books = [book for book in books if summaries[book.id]["status"] == target]

        _sort_books(books, sort, summaries)

        if not books:
            console.print("[yellow]Library is empty[/yellow]")
            return

        table = Table(title="Library")
        table.add_column("ID", justify="right")
        table.add_column("Title")
        table.add_column("Status")
        table.add_column("Progress")
        table.add_column("Position")

        for book in books:
            summary = summaries[book.id]
            position = summary["position"]
            total = summary["total"]

            if total > 0:
                progress_text = f"{position / total * 100:.1f}%"
                position_text = f"{format_seconds(position)} / {format_seconds(total)}"
            else:
                progress_text = "-"
                position_text = "-"

            table.add_row(
                str(book.id),
                escape(book.title),
                summary["status"],
                progress_text,
                position_text,
            )

    console.print(table)


@app.command()
def bookmarks(book_id: int) -> None:
    with Session(engine) as session:
        book = session.get(Book, book_id)

        if book is None:
            console.print("[red]Book not found[/red]")
            raise typer.Exit(code=1)

    items = list_bookmarks(book_id)

    if not items:
        console.print("[yellow]No bookmarks[/yellow]")
        return

    console.print(f"[green]Bookmarks for:[/green] {escape(book.title)}")

    for item in items:
        console.print(f"{item.id}: file={item.file_index} | pos={format_seconds(item.position)}")


@app.command("goto-bookmark")
def goto_bookmark_command(bookmark_id: int) -> None:
    bookmark = get_bookmark(bookmark_id)

    if bookmark is None:
        console.print("[red]Bookmark not found[/red]")
        raise typer.Exit(code=1)

    playback_repository.save_position(
        book_id=bookmark.book_id,
        file_index=bookmark.file_index,
        position=bookmark.position,
        speed=1.0,
    )

    console.print(
        f"[green]Moved to bookmark:[/green] "
        f"file={bookmark.file_index} | "
        f"pos={format_seconds(bookmark.position)}"
    )

    play(bookmark.book_id)


@app.command("delete-bookmark")
def delete_bookmark_command(
    bookmark_id: int,
    force: bool = typer.Option(False, "--force", "-f"),
) -> None:
    bookmark = get_bookmark(bookmark_id)

    if bookmark is None:
        console.print("[red]Bookmark not found[/red]")
        raise typer.Exit(code=1)

    if not force:
        confirm = typer.confirm(
            f"Delete bookmark {bookmark_id} "
            f"(file={bookmark.file_index}, pos={format_seconds(bookmark.position)})?"
        )
        if not confirm:
            console.print("[green]Cancelled[/green]")
            raise typer.Exit()

    deleted = delete_bookmark(bookmark_id)

    if deleted:
        console.print("[red]Bookmark deleted[/red]")
    else:
        console.print("[red]Bookmark not found[/red]")
        raise typer.Exit(code=1)


@app.command("set-speed")
def set_speed(book_id: int, speed: float) -> None:
    if speed < 0.5 or speed > 3.0:
        console.print("[red]Speed must be between 0.5 and 3.0[/red]")
        raise typer.Exit(code=1)

    with Session(engine) as session:
        book = session.get(Book, book_id)

        if book is None:
            console.print("[red]Book not found[/red]")
            raise typer.Exit(code=1)

    state = playback_repository.load_position(book_id)

    file_index = state.file_index if state else 1
    position = state.position if state else 0.0

    playback_repository.save_position(
        book_id=book_id,
        file_index=file_index,
        position=position,
        speed=speed,
    )

    console.print(f"[green]Speed set:[/green] {speed:.1f}x")


@app.command("reset-db")
def reset_db(force: bool = typer.Option(False, "--force", "-f")) -> None:
    """
    Delete the database file.
    """

    if not DB_PATH.exists():
        console.print("[yellow]Database does not exist[/yellow]")
        return

    if not force:
        confirm = typer.confirm("Are you sure you want to delete the database?")
        if not confirm:
            console.print("[green]Cancelled[/green]")
            raise typer.Exit()

    DB_PATH.unlink()

    console.print("[red]Database deleted[/red]")


@app.command("files")
def list_files(book_id: int) -> None:
    with Session(engine) as session:
        book = session.get(Book, book_id)

        if book is None:
            console.print("[red]Book not found[/red]")
            raise typer.Exit(code=1)

        book_files = session.exec(
            select(BookFile).where(BookFile.book_id == book_id).order_by(BookFile.index)
        ).all()

    if not book_files:
        console.print("[yellow]Book has no files[/yellow]")
        return

    book_path = Path(book.path)

    console.print(f"[green]{escape(book.title)}[/green]")

    for book_file in book_files:
        file_path = Path(book_file.path)

        try:
            display_path = file_path.relative_to(book_path)
        except ValueError:
            display_path = file_path

        console.print(f"{book_file.index:04d}: {escape(str(display_path))}")


@app.command()
def status(book_id: int) -> None:
    with Session(engine) as session:
        book = session.get(Book, book_id)

        if book is None:
            console.print("[red]Book not found[/red]")
            raise typer.Exit(code=1)

        book_files = session.exec(
            select(BookFile).where(BookFile.book_id == book_id).order_by(BookFile.index)
        ).all()

    if not book_files:
        console.print("[yellow]Book has no files[/yellow]")
        return

    state = playback_repository.load_position(book_id)

    console.print(f"[green]Book:[/green] {escape(book.title)}")

    book_status, book_position, total_duration = book_progress(book_files, state)

    console.print(f"[green]Status:[/green] {book_status}")

    if state is None:
        return

    console.print(f"[green]File:[/green] {state.file_index} / {len(book_files)}")

    current_file = next(
        (book_file for book_file in book_files if book_file.index == state.file_index),
        None,
    )

    console.print(
        f"[green]File position:[/green] "
        f"{format_seconds(state.position)}"
        f" / {format_seconds(current_file.duration if current_file else 0)}"
    )

    console.print(
        f"[green]Book position:[/green] "
        f"{format_seconds(book_position)}"
        f" / {format_seconds(total_duration)}"
    )

    progress = book_position / total_duration * 100 if total_duration else 0
    console.print(f"[green]Progress:[/green] {progress:.1f}%")
    console.print(f"[green]Speed:[/green] {state.speed:.1f}x")


@app.command("reset-progress")
def reset_progress(
    book_id: int,
    force: bool = typer.Option(False, "--force", "-f"),
) -> None:
    with Session(engine) as session:
        book = session.get(Book, book_id)

        if book is None:
            console.print("[red]Book not found[/red]")
            raise typer.Exit(code=1)

    state = playback_repository.load_position(book_id)

    if state is None:
        console.print("[yellow]Progress already empty[/yellow]")
        return

    if not force:
        confirm = typer.confirm(f"Reset progress for '{book.title}'?")
        if not confirm:
            console.print("[green]Cancelled[/green]")
            raise typer.Exit()

    playback_repository.save_position(book_id, file_index=1, position=0.0, speed=1.0)

    console.print("[red]Progress reset[/red]")


if __name__ == "__main__":
    app()
