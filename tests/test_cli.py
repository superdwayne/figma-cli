"""CLI integration tests for cli-anything-figma."""
import json
from unittest.mock import patch, MagicMock

import pytest
from click.testing import CliRunner

from cli_anything_figma.cli import cli


# ── Helpers ──────────────────────────────────────────────────

def invoke(runner, args, **kwargs):
    """Invoke the CLI and return result."""
    return runner.invoke(cli, args, obj={}, catch_exceptions=False, **kwargs)


def invoke_json(runner, args):
    """Invoke with --json and parse output."""
    result = invoke(runner, ["--json"] + args)
    assert result.exit_code == 0, f"Exit {result.exit_code}: {result.output}"
    return json.loads(result.output)


# ── Version / Help ───────────────────────────────────────────

def test_version(runner):
    result = invoke(runner, ["--version"])
    assert "cli-anything-figma" in result.output


def test_help(runner):
    result = invoke(runner, ["--help"])
    assert "file" in result.output
    assert "export" in result.output
    assert "component" in result.output
    assert "config" in result.output


# ── Me ───────────────────────────────────────────────────────

@patch("cli_anything_figma.api.FigmaClient.get_me")
def test_me_json(mock_get_me, runner, sample_me_response):
    mock_get_me.return_value = sample_me_response
    data = invoke_json(runner, ["me"])
    assert data["handle"] == "testuser"
    assert data["email"] == "test@example.com"


@patch("cli_anything_figma.api.FigmaClient.get_me")
def test_me_table(mock_get_me, runner, sample_me_response):
    mock_get_me.return_value = sample_me_response
    result = invoke(runner, ["me"])
    assert result.exit_code == 0
    assert "testuser" in result.output


# ── File ─────────────────────────────────────────────────────

@patch("cli_anything_figma.api.FigmaClient.get_file")
def test_file_info_json(mock_get_file, runner, sample_file_response):
    mock_get_file.return_value = sample_file_response
    data = invoke_json(runner, ["file", "--file", "abc123", "info"])
    assert data["name"] == "Test Design File"
    assert data["pages"] == 2


@patch("cli_anything_figma.api.FigmaClient.get_file")
def test_file_list_pages_json(mock_get_file, runner, sample_file_response):
    mock_get_file.return_value = sample_file_response
    data = invoke_json(runner, ["file", "--file", "abc123", "list-pages"])
    assert len(data) == 2
    assert data[0]["name"] == "Page 1"
    assert data[1]["name"] == "Page 2"


@patch("cli_anything_figma.api.FigmaClient.get_file")
def test_file_tree_json(mock_get_file, runner, sample_file_response):
    mock_get_file.return_value = sample_file_response
    data = invoke_json(runner, ["file", "--file", "abc123", "tree"])
    assert len(data) >= 2  # at least pages


@patch("cli_anything_figma.api.FigmaClient.get_file")
def test_file_info_table(mock_get_file, runner, sample_file_response):
    mock_get_file.return_value = sample_file_response
    result = invoke(runner, ["file", "--file", "abc123", "info"])
    assert result.exit_code == 0
    assert "Test Design File" in result.output


# ── Comments ─────────────────────────────────────────────────

@patch("cli_anything_figma.api.FigmaClient.get_comments")
def test_comment_list_json(mock_get, runner, sample_comments_response):
    mock_get.return_value = sample_comments_response
    data = invoke_json(runner, ["comment", "--file", "abc123", "list"])
    assert len(data) == 2
    assert data[0]["user"] == "alice"


@patch("cli_anything_figma.api.FigmaClient.post_comment")
def test_comment_post_json(mock_post, runner):
    mock_post.return_value = {"id": "c3", "message": "Nice work!"}
    data = invoke_json(runner, ["comment", "--file", "abc123", "post", "-m", "Nice work!"])
    assert data["id"] == "c3"


@patch("cli_anything_figma.api.FigmaClient.delete_comment")
def test_comment_delete_json(mock_del, runner):
    mock_del.return_value = {"status": "deleted"}
    data = invoke_json(runner, ["comment", "--file", "abc123", "delete", "--comment-id", "c1"])
    assert data["status"] == "deleted"


# ── Components ───────────────────────────────────────────────

@patch("cli_anything_figma.api.FigmaClient.get_file_components")
def test_component_list_json(mock_get, runner, sample_components_response):
    mock_get.return_value = sample_components_response
    data = invoke_json(runner, ["component", "list", "--file", "abc123"])
    assert len(data) == 2
    assert data[0]["name"] == "Button"


@patch("cli_anything_figma.api.FigmaClient.get_component")
def test_component_get_json(mock_get, runner):
    mock_get.return_value = {
        "meta": {"key": "comp1", "name": "Button", "file_key": "abc", "node_id": "1:0"}
    }
    data = invoke_json(runner, ["component", "get", "--key", "comp1"])
    assert data["name"] == "Button"


# ── Styles ───────────────────────────────────────────────────

@patch("cli_anything_figma.api.FigmaClient.get_file_styles")
def test_style_list_json(mock_get, runner, sample_styles_response):
    mock_get.return_value = sample_styles_response
    data = invoke_json(runner, ["style", "list", "--file", "abc123"])
    assert len(data) == 2
    assert data[0]["style_type"] == "FILL"


@patch("cli_anything_figma.api.FigmaClient.get_style")
def test_style_get_json(mock_get, runner):
    mock_get.return_value = {
        "meta": {"key": "s1", "name": "Primary Blue", "style_type": "FILL"}
    }
    data = invoke_json(runner, ["style", "get", "--key", "s1"])
    assert data["name"] == "Primary Blue"


# ── Versions ─────────────────────────────────────────────────

@patch("cli_anything_figma.api.FigmaClient.get_file_versions")
def test_version_list_json(mock_get, runner, sample_versions_response):
    mock_get.return_value = sample_versions_response
    data = invoke_json(runner, ["version", "--file", "abc123", "list"])
    assert len(data) == 2
    assert data[0]["id"] == "v1"


# ── Variables ────────────────────────────────────────────────

@patch("cli_anything_figma.api.FigmaClient.get_local_variables")
def test_variable_list_json(mock_get, runner, sample_variables_response):
    mock_get.return_value = sample_variables_response
    data = invoke_json(runner, ["variable", "--file", "abc123", "list"])
    assert len(data["variables"]) == 2
    assert data["variables"][0]["name"] in ("primary-color", "spacing-md")


@patch("cli_anything_figma.api.FigmaClient.get_local_variables")
def test_variable_collections_json(mock_get, runner, sample_variables_response):
    mock_get.return_value = sample_variables_response
    data = invoke_json(runner, ["variable", "--file", "abc123", "collections"])
    assert len(data) == 1
    assert data[0]["name"] == "Design Tokens"


# ── Config ───────────────────────────────────────────────────

def test_config_show(runner):
    result = invoke(runner, ["config", "show"])
    assert result.exit_code == 0


@patch("cli_anything_figma.api.FigmaClient.get_me")
def test_config_check_json(mock_get_me, runner, sample_me_response):
    mock_get_me.return_value = sample_me_response
    data = invoke_json(runner, ["config", "check"])
    assert data["status"] == "ok"
    assert data["user"] == "testuser"


# ── Export URLs ──────────────────────────────────────────────

@patch("cli_anything_figma.api.FigmaClient.get_images")
def test_export_urls_json(mock_get, runner):
    mock_get.return_value = {
        "images": {
            "1:0": "https://example.com/image.png",
            "1:1": "https://example.com/image2.png",
        }
    }
    data = invoke_json(runner, ["export", "--file", "abc123", "urls", "--ids", "1:0,1:1"])
    assert len(data) == 2
    assert data[0]["node_id"] == "1:0"


# ── Project ──────────────────────────────────────────────────

@patch("cli_anything_figma.api.FigmaClient.get_team_projects")
def test_project_list_json(mock_get, runner):
    mock_get.return_value = {
        "projects": [
            {"id": "p1", "name": "Project Alpha"},
            {"id": "p2", "name": "Project Beta"},
        ]
    }
    data = invoke_json(runner, ["project", "list", "--team", "team1"])
    assert len(data) == 2
    assert data[0]["name"] == "Project Alpha"


@patch("cli_anything_figma.api.FigmaClient.get_project_files")
def test_project_files_json(mock_get, runner):
    mock_get.return_value = {
        "files": [
            {"key": "f1", "name": "Design System", "last_modified": "2025-01-15T12:00:00Z"},
        ]
    }
    data = invoke_json(runner, ["project", "files", "--project-id", "p1"])
    assert len(data) == 1
    assert data[0]["name"] == "Design System"
