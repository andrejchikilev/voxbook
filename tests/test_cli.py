from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from voxbook.cli import app
from voxbook.library.models import Book

runner = CliRunner()


def test_volume_get_with_active_player() -> None:
    with patch("voxbook.cli.PlayerService") as mock_service_class:
        service = Mock()
        service.get_volume.return_value = 75.0
        mock_service_class.return_value = service

        result = runner.invoke(app, ["volume"])

    assert result.exit_code == 0
    assert "Volume: 75" in result.output


def test_volume_get_without_active_player() -> None:
    with patch("voxbook.cli.PlayerService") as mock_service_class:
        service = Mock()
        service.get_volume.return_value = None
        mock_service_class.return_value = service

        result = runner.invoke(app, ["volume"])

    assert result.exit_code == 1
    assert "No active player" in result.output


def test_volume_set() -> None:
    with patch("voxbook.cli.PlayerService") as mock_service_class:
        service = Mock()
        service.get_volume.return_value = 50.0
        mock_service_class.return_value = service

        result = runner.invoke(app, ["volume", "65"])

    assert result.exit_code == 0
    assert "Volume set: 65" in result.output
    service.set_volume.assert_called_once_with(65.0)


def test_volume_set_without_active_player() -> None:
    with patch("voxbook.cli.PlayerService") as mock_service_class:
        service = Mock()
        service.get_volume.return_value = None
        mock_service_class.return_value = service

        result = runner.invoke(app, ["volume", "65"])

    assert result.exit_code == 1
    assert "No active player" in result.output
    service.set_volume.assert_not_called()


def test_volume_set_rejects_out_of_range() -> None:
    with patch("voxbook.cli.PlayerService") as mock_service_class:
        service = Mock()
        mock_service_class.return_value = service

        result = runner.invoke(app, ["volume", "101"])

    assert result.exit_code == 2
    service.set_volume.assert_not_called()

@pytest.fixture(name="cli_runner")
def _cli_runner():
    return CliRunner()


class TestSearch:
    """Tests for search command."""

    # pylint: disable=redefined-outer-name

    @patch("voxbook.cli.engine")
    @patch("voxbook.cli.Session")
    def test_search_by_title(self, mock_session_cls, _mock_engine, cli_runner):
        """Test searching by title."""
        book = Book(id=1, title="Dune", author="Frank Herbert", series=None)
        mock_session = Mock()
        mock_session.exec.return_value.all.return_value = [book]
        mock_session_cls.return_value.__enter__.return_value = mock_session

        result = cli_runner.invoke(app, ["search", "Dune"])

        assert result.exit_code == 0
        assert "Dune" in result.output
        assert "Frank Herbert" in result.output

    @patch("voxbook.cli.engine")
    @patch("voxbook.cli.Session")
    def test_search_by_author(self, mock_session_cls, _mock_engine, cli_runner):
        """Test searching by author."""
        book = Book(id=2, title="Neuromancer", author="William Gibson", series=None)
        mock_session = Mock()
        mock_session.exec.return_value.all.return_value = [book]
        mock_session_cls.return_value.__enter__.return_value = mock_session

        result = cli_runner.invoke(app, ["search", "gibson"])

        assert result.exit_code == 0
        assert "William Gibson" in result.output
        assert "Neuromancer" in result.output

    @patch("voxbook.cli.engine")
    @patch("voxbook.cli.Session")
    def test_search_by_series(self, mock_session_cls, _mock_engine, cli_runner):
        """Test searching by series."""
        book = Book(id=3, title="The Fellowship of the Ring", author="Tolkien", series="LOTR")
        mock_session = Mock()
        mock_session.exec.return_value.all.return_value = [book]
        mock_session_cls.return_value.__enter__.return_value = mock_session

        result = cli_runner.invoke(app, ["search", "LOTR"])

        assert result.exit_code == 0
        assert "LOTR" in result.output

    @patch("voxbook.cli.engine")
    @patch("voxbook.cli.Session")
    def test_search_no_results(self, mock_session_cls, _mock_engine, cli_runner):
        """Test search with no results."""
        mock_session = Mock()
        mock_session.exec.return_value.all.return_value = []
        mock_session_cls.return_value.__enter__.return_value = mock_session

        result = cli_runner.invoke(app, ["search", "missing"])

        assert result.exit_code == 0
        assert "Nothing found" in result.output


class TestSetBook:
    """Tests for set-book command."""

    @patch("voxbook.cli.engine")
    @patch("voxbook.cli.Session")
    def test_set_book_updates_metadata(self, mock_session_cls, _mock_engine, cli_runner):
        """Test updating book metadata."""
        book = Book(id=1, title="Test", author=None, series=None, narrator=None)
        mock_session = Mock()
        mock_session.get.return_value = book
        mock_session_cls.return_value.__enter__.return_value = mock_session

        result = cli_runner.invoke(app, [
            "set-book", "1",
            "--author", "Author Name",
            "--series", "Series Name",
            "--narrator", "Narrator Name",
        ])

        assert result.exit_code == 0
        assert book.author == "Author Name"
        assert book.series == "Series Name"
        assert book.narrator == "Narrator Name"
        assert "Updated book 1" in result.output
        mock_session.commit.assert_called_once()

    @patch("voxbook.cli.engine")
    @patch("voxbook.cli.Session")
    def test_set_book_missing_book(self, mock_session_cls, _mock_engine, cli_runner):
        """Test set-book when book does not exist."""
        mock_session = Mock()
        mock_session.get.return_value = None
        mock_session_cls.return_value.__enter__.return_value = mock_session

        result = cli_runner.invoke(app, ["set-book", "99", "--author", "Author"])

        assert result.exit_code == 1
        assert "Book not found" in result.output


class TestBookInfo:
    """Tests for book-info command."""

    @patch("voxbook.cli.engine")
    @patch("voxbook.cli.Session")
    def test_book_info_displays_metadata(self, mock_session_cls, _mock_engine, cli_runner):
        """Test displaying book metadata."""
        book = Book(
            id=1,
            title="The Book",
            author="The Author",
            series="The Series",
            narrator="The Narrator",
            path="/test/path",
        )
        mock_session = Mock()
        mock_session.get.return_value = book
        mock_session_cls.return_value.__enter__.return_value = mock_session

        result = cli_runner.invoke(app, ["book-info", "1"])

        assert result.exit_code == 0
        assert "The Book" in result.output
        assert "The Author" in result.output
        assert "The Series" in result.output
        assert "The Narrator" in result.output
        assert "/test/path" in result.output
