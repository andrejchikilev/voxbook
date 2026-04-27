"""Pytest configuration and shared fixtures."""
from pathlib import Path
from unittest.mock import Mock

import pytest
from sqlmodel import Session


@pytest.fixture
def tmp_library(tmp_path: Path) -> Path:
    """Create a temporary library directory with sample structure."""
    library = tmp_path / "library"
    library.mkdir()
    return library


@pytest.fixture
def mock_mpv() -> Mock:
    """Create a mock MPV player."""
    mpv = Mock()
    mpv.play = Mock()
    mpv.pause = Mock()
    mpv.stop = Mock()
    mpv.seek = Mock()
    mpv.time_pos = 0
    mpv.duration = 3600
    return mpv


@pytest.fixture
def mock_session() -> Mock:
    """Create a mock database session."""
    session = Mock(spec=Session)
    session.exec = Mock()
    session.add = Mock()
    session.commit = Mock()
    session.refresh = Mock()
    return session
