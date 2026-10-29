from pathlib import Path

import typer
from rich.console import Console
from rich.markup import escape
from rich.table import Table
from sqlalchemy import or_
from sqlmodel import Session, select

from voxbook.helpers import book_position_to_file_position, format_seconds, parse_timestamp
from voxbook.library.models import Book, BookFile, LibraryRoot
from voxbook.library.repository import (
    delete_bookmark,
    get_bookmark,
    list_bookmarks,
)
from voxbook.library.repository import (
    remove_book as remove_book_from_library,
)
from voxbook.library.scanner import rescan_libraries, scan_library
from voxbook.playback.player_service import PlayerService
from voxbook.playback.repository import PlaybackRepository
from voxbook.storage.db import engine, get_db_path, init_db

app = typer.Typer()
console = Console()
playback_repository = PlaybackRepository()


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
def rescan() -> None:
    saved_roots = rescan_libraries()

    if not saved_roots:
        console.print("[yellow]No library roots configured. Use `voxbook scan <path>`.[/yellow]")
        raise typer.Exit()

    for root in saved_roots:
        console.print(f"Rescanned directory: {escape(str(root))}")


@app.command()
def roots(
    remove: str | None = typer.Option(None, "--remove", "-r", help="Remove a library root path"),
) -> None:
    with Session(engine) as session:
        if remove is not None:
            normalized = str(Path(remove).expanduser().resolve())
            existing = session.exec(
                select(LibraryRoot).where(LibraryRoot.path == normalized)
            ).first()

            if existing is None:
                console.print("[yellow]Library root not found[/yellow]")
                raise typer.Exit(code=1)

            session.delete(existing)
            session.commit()
            console.print(f"[green]Removed library root:[/green] {escape(normalized)}")
            return

        items = session.exec(select(LibraryRoot).order_by(LibraryRoot.added_at)).all()

        if not items:
            console.print("[yellow]No library roots configured[/yellow]")
            return

        table = Table(title="Library Roots")
        table.add_column("ID", justify="right")
        table.add_column("Path")
        table.add_column("Added")

        for item in items:
            table.add_row(
                str(item.id),
                escape(item.path),
                escape(item.added_at.strftime("%Y-%m-%d %H:%M:%S")),
            )

        console.print(table)


@app.command()
def search(query: str) -> None:
    pattern = f"%{query}%"

    with Session(engine) as session:
        books = session.exec(
            select(Book)
            .where(
                or_(
                    Book.title.ilike(pattern),
                    Book.author.ilike(pattern),
                    Book.series.ilike(pattern),
                )
            )
            .order_by(Book.title)
        ).all()

    if not books:
        console.print("[yellow]Nothing found[/yellow]")
        return

    for book in books:
        author = book.author or "Unknown"
        series_part = f" ({book.series})" if book.series else ""
        console.print(f"{book.id}: {escape(author)} — {escape(book.title)}{escape(series_part)}")


@app.command("list")
def list_books() -> None:
    with Session(engine) as session:
        books = session.exec(select(Book).order_by(Book.title)).all()

        if not books:
            console.print("[yellow]Library is empty[/yellow]")
            return

        table = Table(title="Library")
        table.add_column("ID", justify="right")
        table.add_column("Title")
        table.add_column("Author")
        table.add_column("Progress")
        table.add_column("Position")

        for book in books:
            book_files = session.exec(
                select(BookFile).where(BookFile.book_id == book.id).order_by(BookFile.index)
            ).all()

            state = playback_repository.load_position(book.id)

            if not state or not book_files:
                progress_text = "not started"
                position_text = "-"
            else:
                previous_duration = sum(
                    book_file.duration
                    for book_file in book_files
                    if book_file.index < state.file_index
                )

                total_duration = sum(book_file.duration for book_file in book_files)
                book_position = previous_duration + state.position

                progress = book_position / total_duration * 100 if total_duration else 0

                progress_text = f"{progress:.1f}%"
                position_text = (
                    f"{format_seconds(book_position)} / {format_seconds(total_duration)}"
                )

            table.add_row(
                str(book.id),
                escape(book.title),
                escape(book.author or "—"),
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


@app.command()
def goto(book_id: int, position: str) -> None:
    with Session(engine) as session:
        book = session.get(Book, book_id)

        if book is None:
            console.print("[red]Book not found[/red]")
            raise typer.Exit(code=1)

        book_files = session.exec(
            select(BookFile).where(BookFile.book_id == book_id).order_by(BookFile.index)
        ).all()

    if not book_files:
        console.print("[red]Book has no files[/red]")
        raise typer.Exit(code=1)

    try:
        book_position = parse_timestamp(position)
    except ValueError as error:
        console.print(f"[red]Invalid position: {error}[/red]")
        raise typer.Exit(code=1) from error

    file_index, file_position = book_position_to_file_position(list(book_files), book_position)

    existing_state = playback_repository.load_position(book_id)
    saved_speed = existing_state.speed if existing_state else 1.0

    playback_repository.save_position(
        book_id=book_id,
        file_index=file_index,
        position=file_position,
        speed=saved_speed,
    )

    console.print(
        f"[green]Goto:[/green] {format_seconds(book_position)} "
        f"(file {file_index}, pos {format_seconds(file_position)})"
    )

    play(book_id)


@app.command("goto-bookmark")
def goto_bookmark_command(bookmark_id: int) -> None:
    bookmark = get_bookmark(bookmark_id)

    if bookmark is None:
        console.print("[red]Bookmark not found[/red]")
        raise typer.Exit(code=1)

    existing_state = playback_repository.load_position(bookmark.book_id)
    saved_speed = existing_state.speed if existing_state else 1.0

    playback_repository.save_position(
        book_id=bookmark.book_id,
        file_index=bookmark.file_index,
        position=bookmark.position,
        speed=saved_speed,
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


@app.command("book-info")
def book_info(book_id: int) -> None:
    with Session(engine) as session:
        book = session.get(Book, book_id)

        if book is None:
            console.print("[red]Book not found[/red]")
            raise typer.Exit(code=1)

    console.print(f"[green]Book:[/green] {escape(book.title)}")
    console.print(f"[green]Author:[/green] {escape(book.author or '—')}")
    console.print(f"[green]Series:[/green] {escape(book.series or '—')}")
    console.print(f"[green]Narrator:[/green] {escape(book.narrator or '—')}")
    console.print(f"[green]Path:[/green] {escape(book.path)}")


@app.command("set-book")
def set_book(
    book_id: int,
    author: str | None = typer.Option(None, "--author"),
    series: str | None = typer.Option(None, "--series"),
    narrator: str | None = typer.Option(None, "--narrator"),
) -> None:
    with Session(engine) as session:
        book = session.get(Book, book_id)

        if book is None:
            console.print("[red]Book not found[/red]")
            raise typer.Exit(code=1)

        if author is not None:
            book.author = author
        if series is not None:
            book.series = series
        if narrator is not None:
            book.narrator = narrator

        session.add(book)
        session.commit()

    console.print(f"[green]Updated book {book_id}[/green]")


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


@app.command()
def remove_book(
    book_id: int,
    force: bool = typer.Option(False, "--force", "-f"),
) -> None:
    with Session(engine) as session:
        book = session.get(Book, book_id)

        if book is None:
            console.print("[red]Book not found[/red]")
            raise typer.Exit(code=1)

        book_files = session.exec(
            select(BookFile).where(BookFile.book_id == book_id)
        ).all()
        file_count = len(book_files)
        bookmark_count = len(list_bookmarks(book_id))

    if not force:
        confirm = typer.confirm(
            f"Delete book '{book.title}' "
            f"({file_count} files, {bookmark_count} bookmarks)?"
        )
        if not confirm:
            console.print("[green]Cancelled[/green]")
            raise typer.Exit()

    result = remove_book_from_library(book_id)

    if not result[0]:
        console.print("[red]Book not found[/red]")
        raise typer.Exit(code=1)

    _, removed_files, removed_bookmarks, progress_removed = result

    console.print(
        f"[red]Deleted book[/red]: {escape(book.title)} "
        f"({removed_files} files, {removed_bookmarks} bookmarks, "
        f"progress {'reset' if progress_removed else 'was empty'})"
    )


@app.command("reset-db")
def reset_db(force: bool = typer.Option(False, "--force", "-f")) -> None:
    """
    Delete the database file.
    """

    db_path = get_db_path()

    if not db_path.exists():
        console.print("[yellow]Database does not exist[/yellow]")
        return

    if not force:
        confirm = typer.confirm("Are you sure you want to delete the database?")
        if not confirm:
            console.print("[green]Cancelled[/green]")
            raise typer.Exit()

    db_path.unlink()

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

    if state is None:
        console.print("[yellow]Progress:[/yellow] not started")
        return

    current_file = next(
        (book_file for book_file in book_files if book_file.index == state.file_index),
        None,
    )

    previous_duration = sum(
        book_file.duration for book_file in book_files if book_file.index < state.file_index
    )

    total_duration = sum(book_file.duration for book_file in book_files)
    book_position = previous_duration + state.position

    console.print(f"[green]File:[/green] {state.file_index} / {len(book_files)}")

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


@app.command()
def volume(
    level: float | None = typer.Argument(None, min=0.0, max=100.0),
) -> None:
    player_service = PlayerService()

    if level is None:
        current_volume = player_service.get_volume()

        if current_volume is None:
            console.print("[yellow]No active player[/yellow]")
            raise typer.Exit(code=1)

        console.print(f"[green]Volume:[/green] {current_volume:.0f}")
        return

    if player_service.get_volume() is None:
        console.print("[yellow]No active player[/yellow]")
        raise typer.Exit(code=1)

    player_service.set_volume(level)
    console.print(f"[green]Volume set:[/green] {level:.0f}")


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
