"""
Shared fixtures for the OKAS backend test suite.

All tests run against a mocked database — no live MySQL connection required.
The `client` fixture provides a FastAPI TestClient with DB dependencies patched.
"""
import pytest
from unittest.mock import MagicMock, patch
from contextlib import contextmanager
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def client():
    """TestClient with no real DB calls."""
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def mock_db():
    """
    Context-manager mock for app.db.get_db.
    Returns a mock connection whose cursor() returns a configurable mock cursor.
    """
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

    @contextmanager
    def _fake_get_db():
        yield mock_conn

    with patch("app.db.get_db", side_effect=_fake_get_db):
        yield mock_cursor


@pytest.fixture()
def mock_orm_session():
    """Patch SQLAlchemy ORM session used by projects / roles routes."""
    mock_session = MagicMock()
    with patch("app.models.base.get_session", return_value=iter([mock_session])):
        yield mock_session
