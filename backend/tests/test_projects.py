"""Tests for /we-okas/projects endpoints."""
import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

from app.main import app
from app.db import get_orm_session


def _make_orm_session(query_results=None, count_val=0):
    """
    Build a mock SQLAlchemy ORM session.
    All query-chaining methods return the same mock_query so that
    any combination of .filter/.outerjoin/.join/.order_by/etc. stays mockable.
    """
    mock_db = MagicMock(spec=Session)
    mock_query = MagicMock()
    for chain_method in ("filter", "outerjoin", "join", "options",
                         "order_by", "offset", "limit", "distinct"):
        getattr(mock_query, chain_method).return_value = mock_query
    mock_query.first.return_value = None
    mock_query.count.return_value = count_val
    mock_query.all.return_value = query_results or []
    mock_db.query.return_value = mock_query
    mock_db.add = MagicMock()
    mock_db.flush = MagicMock()
    mock_db.commit = MagicMock()
    return mock_db


@pytest.fixture(autouse=True)
def clear_overrides():
    """Reset dependency overrides after every test."""
    yield
    app.dependency_overrides.clear()


class TestListProjects:
    def test_returns_200(self, client):
        mock_db = _make_orm_session()
        app.dependency_overrides[get_orm_session] = lambda: mock_db
        r = client.get("/we-okas/projects")
        assert r.status_code == 200

    def test_response_envelope(self, client):
        mock_db = _make_orm_session()
        app.dependency_overrides[get_orm_session] = lambda: mock_db
        body = client.get("/we-okas/projects").json()
        assert "status" in body
        assert "message" in body
        assert "body" in body

    def test_body_has_pagination_keys(self, client):
        mock_db = _make_orm_session()
        app.dependency_overrides[get_orm_session] = lambda: mock_db
        payload = client.get("/we-okas/projects").json()["body"]
        assert "total" in payload
        assert "page" in payload
        assert "page_size" in payload
        assert "projects" in payload

    def test_status_filter_accepted(self, client):
        mock_db = _make_orm_session()
        app.dependency_overrides[get_orm_session] = lambda: mock_db
        r = client.get("/we-okas/projects?status=active")
        assert r.status_code == 200

    def test_invalid_status_returns_400(self, client):
        mock_db = _make_orm_session()
        app.dependency_overrides[get_orm_session] = lambda: mock_db
        r = client.get("/we-okas/projects?status=invalid_status")
        assert r.status_code == 400

    def test_project_type_filter_accepted(self, client):
        mock_db = _make_orm_session()
        app.dependency_overrides[get_orm_session] = lambda: mock_db
        r = client.get("/we-okas/projects?project_type=residential")
        assert r.status_code == 200

    def test_invalid_project_type_returns_400(self, client):
        mock_db = _make_orm_session()
        app.dependency_overrides[get_orm_session] = lambda: mock_db
        r = client.get("/we-okas/projects?project_type=unknown")
        assert r.status_code == 400

    def test_empty_result_total_is_zero(self, client):
        mock_db = _make_orm_session(query_results=[], count_val=0)
        app.dependency_overrides[get_orm_session] = lambda: mock_db
        body = client.get("/we-okas/projects").json()["body"]
        assert body["total"] == 0
        assert body["projects"] == []


class TestCreateProject:
    _valid_payload = {
        "name": "Test Project",
        "project_type": "residential",
        "homeowner": {"email": "owner@test.com", "full_name": "John Doe"},
    }

    def test_missing_all_fields_returns_422(self, client):
        r = client.post("/we-okas/projects", json={})
        assert r.status_code == 422

    def test_missing_homeowner_returns_422(self, client):
        r = client.post("/we-okas/projects", json={"name": "X", "project_type": "residential"})
        assert r.status_code == 422

    def test_missing_name_returns_422(self, client):
        r = client.post("/we-okas/projects", json={
            "project_type": "residential",
            "homeowner": {"email": "owner@test.com"},
        })
        assert r.status_code == 422

    def test_invalid_project_type_returns_422(self, client):
        payload = {**self._valid_payload, "project_type": "invalid"}
        r = client.post("/we-okas/projects", json=payload)
        assert r.status_code == 422

    def test_empty_homeowner_email_returns_422(self, client):
        # HomeownerInput validates that email is non-empty (not format)
        payload = {**self._valid_payload, "homeowner": {"email": "   "}}
        r = client.post("/we-okas/projects", json=payload)
        assert r.status_code == 422

    def test_valid_payload_passes_validation(self, client):
        mock_db = _make_orm_session()
        app.dependency_overrides[get_orm_session] = lambda: mock_db
        r = client.post("/we-okas/projects", json=self._valid_payload)
        # Reaches DB layer — 201 success or 409 conflict are both valid
        assert r.status_code in (201, 409)

    def test_duplicate_name_returns_409(self, client):
        mock_db = _make_orm_session()
        # Simulate duplicate name found
        mock_db.query.return_value.filter.return_value.first.return_value = MagicMock()
        app.dependency_overrides[get_orm_session] = lambda: mock_db
        r = client.post("/we-okas/projects", json=self._valid_payload)
        assert r.status_code == 409
