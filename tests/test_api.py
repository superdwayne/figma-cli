"""Unit tests for the Figma API client."""
import json
from unittest.mock import patch, MagicMock

import pytest
import responses

from cli_anything_figma.api import FigmaClient, FigmaAPIError, BASE_URL


# ── Client initialization ────────────────────────────────────

def test_client_init_with_token():
    client = FigmaClient(token="test_token")
    assert client.token == "test_token"
    assert client.session.headers["X-Figma-Token"] == "test_token"


def test_client_init_no_token(monkeypatch):
    monkeypatch.delenv("FIGMA_ACCESS_TOKEN", raising=False)
    with patch("cli_anything_figma.api.get_token", return_value=None):
        with pytest.raises(FigmaAPIError) as exc:
            FigmaClient(token=None)
        assert "No access token" in str(exc.value)


# ── API calls ────────────────────────────────────────────────

@responses.activate
def test_get_me():
    responses.add(
        responses.GET,
        f"{BASE_URL}/me",
        json={"id": "u1", "handle": "test", "email": "t@t.com"},
        status=200,
    )
    client = FigmaClient(token="test")
    result = client.get_me()
    assert result["handle"] == "test"


@responses.activate
def test_get_file():
    responses.add(
        responses.GET,
        f"{BASE_URL}/files/abc123",
        json={"name": "My File", "document": {"children": []}},
        status=200,
    )
    client = FigmaClient(token="test")
    result = client.get_file("abc123")
    assert result["name"] == "My File"


@responses.activate
def test_get_file_404():
    responses.add(
        responses.GET,
        f"{BASE_URL}/files/bad",
        json={"err": "Not found", "status": 404},
        status=404,
    )
    client = FigmaClient(token="test")
    with pytest.raises(FigmaAPIError) as exc:
        client.get_file("bad")
    assert exc.value.status_code == 404


@responses.activate
def test_get_images():
    responses.add(
        responses.GET,
        f"{BASE_URL}/images/abc123",
        json={"images": {"1:0": "https://cdn.figma.com/img.png"}},
        status=200,
    )
    client = FigmaClient(token="test")
    result = client.get_images("abc123", ["1:0"], scale=2.0, fmt="png")
    assert "1:0" in result["images"]


@responses.activate
def test_get_comments():
    responses.add(
        responses.GET,
        f"{BASE_URL}/files/abc123/comments",
        json={"comments": [{"id": "c1", "message": "Hello"}]},
        status=200,
    )
    client = FigmaClient(token="test")
    result = client.get_comments("abc123")
    assert len(result["comments"]) == 1


@responses.activate
def test_post_comment():
    responses.add(
        responses.POST,
        f"{BASE_URL}/files/abc123/comments",
        json={"id": "c2", "message": "Test"},
        status=200,
    )
    client = FigmaClient(token="test")
    result = client.post_comment("abc123", "Test")
    assert result["id"] == "c2"


@responses.activate
def test_delete_comment():
    responses.add(
        responses.DELETE,
        f"{BASE_URL}/files/abc123/comments/c1",
        status=204,
    )
    client = FigmaClient(token="test")
    result = client.delete_comment("abc123", "c1")
    assert result["status"] == "deleted"


@responses.activate
def test_get_file_components():
    responses.add(
        responses.GET,
        f"{BASE_URL}/files/abc123/components",
        json={"meta": {"components": [{"key": "k1", "name": "Btn"}]}},
        status=200,
    )
    client = FigmaClient(token="test")
    result = client.get_file_components("abc123")
    assert result["meta"]["components"][0]["name"] == "Btn"


@responses.activate
def test_get_file_styles():
    responses.add(
        responses.GET,
        f"{BASE_URL}/files/abc123/styles",
        json={"meta": {"styles": [{"key": "s1", "name": "Blue"}]}},
        status=200,
    )
    client = FigmaClient(token="test")
    result = client.get_file_styles("abc123")
    assert result["meta"]["styles"][0]["name"] == "Blue"


@responses.activate
def test_get_file_versions():
    responses.add(
        responses.GET,
        f"{BASE_URL}/files/abc123/versions",
        json={"versions": [{"id": "v1"}]},
        status=200,
    )
    client = FigmaClient(token="test")
    result = client.get_file_versions("abc123")
    assert len(result["versions"]) == 1


@responses.activate
def test_get_local_variables():
    responses.add(
        responses.GET,
        f"{BASE_URL}/files/abc123/variables/local",
        json={"meta": {"variables": {}, "variableCollections": {}}},
        status=200,
    )
    client = FigmaClient(token="test")
    result = client.get_local_variables("abc123")
    assert "variables" in result["meta"]


@responses.activate
def test_get_team_projects():
    responses.add(
        responses.GET,
        f"{BASE_URL}/teams/t1/projects",
        json={"projects": [{"id": "p1", "name": "Proj"}]},
        status=200,
    )
    client = FigmaClient(token="test")
    result = client.get_team_projects("t1")
    assert result["projects"][0]["name"] == "Proj"


@responses.activate
def test_get_project_files():
    responses.add(
        responses.GET,
        f"{BASE_URL}/projects/p1/files",
        json={"files": [{"key": "f1", "name": "File"}]},
        status=200,
    )
    client = FigmaClient(token="test")
    result = client.get_project_files("p1")
    assert result["files"][0]["name"] == "File"
