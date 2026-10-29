"""Pytest configuration and shared fixtures."""
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock
from urllib.parse import unquote, urlparse

import pytest
from sqlmodel import Session

# Pytest imports conftest.py before collecting test modules, so set the override
# here rather than in a fixture that runs after test modules have been imported.
_TEST_DB_DIR = Path(tempfile.mkdtemp(prefix="voxbook-test-db-"))
_TEST_DB_PATH = _TEST_DB_DIR / "test.db"
os.environ["VOXBOOK_DB_PATH"] = str(_TEST_DB_PATH)


def pytest_sessionstart(session):
    """Reject a pytest session if its configured engine points at the user DB."""
    del session
    from voxbook.storage.db import engine

    engine_path = Path(unquote(urlparse(str(engine.url)).path)).resolve()
    user_db_path = (Path.home() / ".local/share/voxbook/voxbook.db").resolve()
    if engine_path == user_db_path:
        raise RuntimeError("Pytest database engine must not point at the user database")


@pytest.fixture(scope="session", autouse=True)
def _isolated_test_db():
    """Redirect all real database engines to a single test DB for the pytest run."""
    # monkeypatch is function-scoped by default; create a session-scoped helper.
    mp = pytest.MonkeyPatch()

    # Import after the top-level environment override so the module-level engine
    # is created against the test database instead of the user database.
    # Re-bind downstream module-level engine references to the isolated engine.
    import voxbook.cli
    import voxbook.library.repository
    import voxbook.library.scanner
    import voxbook.playback.repository
    import voxbook.playback.status_renderer
    from voxbook.storage.db import engine as db_engine
    from voxbook.storage.db import init_db

    voxbook.storage.db.engine = db_engine
    voxbook.cli.engine = db_engine
    voxbook.playback.repository.engine = db_engine
    voxbook.library.scanner.engine = db_engine
    voxbook.library.repository.engine = db_engine
    voxbook.playback.status_renderer.engine = db_engine

    # Create tables so tests that directly use Session(engine) without calling
    # init_db() still work against the isolated test database.
    init_db()

    yield

    mp.undo()

    try:
        db_engine.dispose()
        _TEST_DB_PATH.unlink(missing_ok=True)
        _TEST_DB_DIR.rmdir()
    except OSError:
        pass


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
