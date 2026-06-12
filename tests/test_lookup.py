"""Tests for shared /api lookup endpoints."""
from unittest.mock import MagicMock, patch
from contextlib import contextmanager


def _patch_lookup_db(rows):
    """
    Patch get_db at the point of use (app.shared_api.routes.lookup),
    not at definition. When a module does `from app.db import get_db`
    it holds its own reference — patching the source has no effect.
    """
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = rows
    mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

    @contextmanager
    def _fake():
        yield mock_conn

    return patch("app.shared_api.routes.lookup.get_db", side_effect=_fake)


class TestListOrganizations:
    def test_empty_db_returns_success(self, client):
        with _patch_lookup_db([]):
            r = client.get("/api/organizations")
        assert r.status_code == 200
        body = r.json()
        assert body["success"] is True
        assert body["data"] == []

    def test_returns_org_rows(self, client):
        rows = [{"id": 1, "name": "Acme", "slug": "acme"}]
        with _patch_lookup_db(rows):
            r = client.get("/api/organizations")
        assert r.status_code == 200
        assert r.json()["data"] == rows

    def test_multiple_orgs(self, client):
        rows = [
            {"id": 1, "name": "Alpha", "slug": "alpha"},
            {"id": 2, "name": "Beta",  "slug": "beta"},
        ]
        with _patch_lookup_db(rows):
            r = client.get("/api/organizations")
        assert len(r.json()["data"]) == 2


class TestListAppUsers:
    def test_empty_returns_success(self, client):
        with _patch_lookup_db([]):
            r = client.get("/api/app-users")
        assert r.status_code == 200
        assert r.json()["data"] == []

    def test_returns_user_rows(self, client):
        rows = [{"id": 1, "full_name": "Alice", "email": "alice@okas.io"}]
        with _patch_lookup_db(rows):
            r = client.get("/api/app-users")
        assert r.json()["data"] == rows


class TestListHomeowners:
    def test_empty_returns_success(self, client):
        with _patch_lookup_db([]):
            r = client.get("/api/homeowners")
        assert r.status_code == 200
        assert r.json()["data"] == []
