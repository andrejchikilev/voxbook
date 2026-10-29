from unittest.mock import Mock, patch

from typer.testing import CliRunner

from voxbook.cli import app

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
        mock_service_class.return_value = service

        result = runner.invoke(app, ["volume", "65"])

    assert result.exit_code == 0
    assert "Volume set: 65" in result.output
    service.set_volume.assert_called_once_with(65.0)


def test_volume_set_rejects_out_of_range() -> None:
    with patch("voxbook.cli.PlayerService") as mock_service_class:
        service = Mock()
        mock_service_class.return_value = service

        result = runner.invoke(app, ["volume", "101"])

    assert result.exit_code == 2
    service.set_volume.assert_not_called()
