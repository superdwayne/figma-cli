"""Shared fixtures for cli-anything-figma tests."""
import os
import pytest
from click.testing import CliRunner


@pytest.fixture
def runner():
    """Click CLI test runner."""
    return CliRunner()


@pytest.fixture(autouse=True)
def mock_token(monkeypatch):
    """Set a dummy token for all tests."""
    monkeypatch.setenv("FIGMA_ACCESS_TOKEN", "figd_test_token_12345")


@pytest.fixture
def sample_file_response():
    """Minimal Figma file response."""
    return {
        "name": "Test Design File",
        "lastModified": "2025-01-15T12:00:00Z",
        "version": "123456789",
        "role": "editor",
        "thumbnailUrl": "https://example.com/thumb.png",
        "document": {
            "id": "0:0",
            "name": "Document",
            "type": "DOCUMENT",
            "children": [
                {
                    "id": "1:0",
                    "name": "Page 1",
                    "type": "CANVAS",
                    "children": [
                        {
                            "id": "2:0",
                            "name": "Frame 1",
                            "type": "FRAME",
                            "children": [],
                        }
                    ],
                },
                {
                    "id": "1:1",
                    "name": "Page 2",
                    "type": "CANVAS",
                    "children": [],
                },
            ],
        },
    }


@pytest.fixture
def sample_comments_response():
    """Minimal comments response."""
    return {
        "comments": [
            {
                "id": "c1",
                "user": {"handle": "alice", "id": "u1"},
                "message": "Looks good!",
                "created_at": "2025-01-10T10:00:00Z",
                "resolved_at": None,
                "parent_id": None,
            },
            {
                "id": "c2",
                "user": {"handle": "bob", "id": "u2"},
                "message": "Can you change the color?",
                "created_at": "2025-01-11T11:00:00Z",
                "resolved_at": None,
                "parent_id": None,
            },
        ]
    }


@pytest.fixture
def sample_components_response():
    """Minimal components response."""
    return {
        "meta": {
            "components": [
                {
                    "key": "comp1",
                    "name": "Button",
                    "description": "Primary button component",
                    "containing_frame": {"name": "Components"},
                },
                {
                    "key": "comp2",
                    "name": "Card",
                    "description": "Card layout",
                    "containing_frame": {"name": "Components"},
                },
            ]
        }
    }


@pytest.fixture
def sample_styles_response():
    """Minimal styles response."""
    return {
        "meta": {
            "styles": [
                {
                    "key": "s1",
                    "name": "Primary Blue",
                    "style_type": "FILL",
                    "description": "Main brand color",
                },
                {
                    "key": "s2",
                    "name": "Heading 1",
                    "style_type": "TEXT",
                    "description": "Large heading style",
                },
            ]
        }
    }


@pytest.fixture
def sample_versions_response():
    """Minimal versions response."""
    return {
        "versions": [
            {
                "id": "v1",
                "label": "Initial",
                "description": "First version",
                "user": {"handle": "alice"},
                "created_at": "2025-01-01T00:00:00Z",
            },
            {
                "id": "v2",
                "label": "",
                "description": "",
                "user": {"handle": "bob"},
                "created_at": "2025-01-15T12:00:00Z",
            },
        ]
    }


@pytest.fixture
def sample_variables_response():
    """Minimal variables response."""
    return {
        "meta": {
            "variables": {
                "var1": {
                    "name": "primary-color",
                    "resolvedType": "COLOR",
                    "variableCollectionId": "col1",
                    "description": "Primary brand color",
                    "remote": False,
                },
                "var2": {
                    "name": "spacing-md",
                    "resolvedType": "FLOAT",
                    "variableCollectionId": "col1",
                    "description": "Medium spacing",
                    "remote": False,
                },
            },
            "variableCollections": {
                "col1": {
                    "name": "Design Tokens",
                    "modes": [{"name": "Light"}, {"name": "Dark"}],
                    "variableIds": ["var1", "var2"],
                    "remote": False,
                }
            },
        }
    }


@pytest.fixture
def sample_me_response():
    """Minimal /me response."""
    return {
        "id": "u123",
        "handle": "testuser",
        "email": "test@example.com",
        "img_url": "https://example.com/avatar.png",
    }
