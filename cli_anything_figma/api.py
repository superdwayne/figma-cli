"""Figma REST API client for cli-anything-figma."""
import json
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import requests

from cli_anything_figma.config import get_token

BASE_URL = "https://api.figma.com/v1"


class FigmaAPIError(Exception):
    """Raised when the Figma API returns an error."""

    def __init__(self, status_code: int, message: str, url: str = ""):
        self.status_code = status_code
        self.url = url
        super().__init__(f"[{status_code}] {message}")


class FigmaClient:
    """Thin wrapper around the Figma REST API."""

    def __init__(self, token: str | None = None):
        self.token = token or get_token()
        if not self.token:
            raise FigmaAPIError(
                401,
                "No access token configured. "
                "Run: figma-cli config set-token <TOKEN> "
                "or set FIGMA_ACCESS_TOKEN env var.",
            )
        self.session = requests.Session()
        self.session.headers.update({"X-Figma-Token": self.token})

    # ── helpers ──────────────────────────────────────────────

    def _get(self, path: str, params: dict | None = None) -> dict:
        url = f"{BASE_URL}{path}"
        resp = self.session.get(url, params=params, timeout=60)
        if not resp.ok:
            body = resp.text
            try:
                body = resp.json().get("err", body)
            except Exception:
                pass
            raise FigmaAPIError(resp.status_code, str(body), url)
        return resp.json()

    def _post(self, path: str, payload: dict | None = None) -> dict:
        url = f"{BASE_URL}{path}"
        resp = self.session.post(url, json=payload, timeout=60)
        if not resp.ok:
            body = resp.text
            try:
                body = resp.json().get("err", body)
            except Exception:
                pass
            raise FigmaAPIError(resp.status_code, str(body), url)
        return resp.json()

    def _delete(self, path: str) -> dict:
        url = f"{BASE_URL}{path}"
        resp = self.session.delete(url, timeout=60)
        if not resp.ok:
            body = resp.text
            try:
                body = resp.json().get("err", body)
            except Exception:
                pass
            raise FigmaAPIError(resp.status_code, str(body), url)
        # Some DELETE endpoints return 204 with no body
        if resp.status_code == 204:
            return {"status": "deleted"}
        return resp.json()

    # ── Me / User ────────────────────────────────────────────

    def get_me(self) -> dict:
        """Get the current user."""
        return self._get("/me")

    # ── Files ────────────────────────────────────────────────

    def get_file(self, file_key: str, **kwargs) -> dict:
        """Get a Figma file by key.

        Optional kwargs: version, ids, depth, geometry,
        plugin_data, branch_data.
        """
        params = {k: v for k, v in kwargs.items() if v is not None}
        return self._get(f"/files/{file_key}", params=params)

    def get_file_nodes(self, file_key: str, node_ids: list[str], **kwargs) -> dict:
        """Get specific nodes from a file."""
        params = {"ids": ",".join(node_ids)}
        params.update({k: v for k, v in kwargs.items() if v is not None})
        return self._get(f"/files/{file_key}/nodes", params=params)

    # ── Images / Export ──────────────────────────────────────

    def get_images(
        self,
        file_key: str,
        node_ids: list[str],
        scale: float = 2.0,
        fmt: str = "png",
        svg_include_id: bool = False,
        svg_simplify_stroke: bool = True,
        use_absolute_bounds: bool = False,
    ) -> dict:
        """Export nodes as images. Returns download URLs."""
        params = {
            "ids": ",".join(node_ids),
            "scale": scale,
            "format": fmt,
        }
        if fmt == "svg":
            params["svg_include_id"] = str(svg_include_id).lower()
            params["svg_simplify_stroke"] = str(svg_simplify_stroke).lower()
        if use_absolute_bounds:
            params["use_absolute_bounds"] = "true"
        return self._get(f"/images/{file_key}", params=params)

    def get_image_fills(self, file_key: str) -> dict:
        """Get download links for images used as fills."""
        return self._get(f"/files/{file_key}/images")

    # ── Comments ─────────────────────────────────────────────

    def get_comments(self, file_key: str) -> dict:
        """List comments on a file."""
        return self._get(f"/files/{file_key}/comments")

    def post_comment(
        self,
        file_key: str,
        message: str,
        client_meta: dict | None = None,
        comment_id: str | None = None,
    ) -> dict:
        """Post a comment on a file. Set comment_id to reply."""
        payload: dict[str, Any] = {"message": message}
        if client_meta:
            payload["client_meta"] = client_meta
        if comment_id:
            payload["comment_id"] = comment_id
        return self._post(f"/files/{file_key}/comments", payload)

    def delete_comment(self, file_key: str, comment_id: str) -> dict:
        """Delete a comment."""
        return self._delete(f"/files/{file_key}/comments/{comment_id}")

    # ── Components & Styles ──────────────────────────────────

    def get_file_components(self, file_key: str) -> dict:
        """List published components in a file."""
        return self._get(f"/files/{file_key}/components")

    def get_file_component_sets(self, file_key: str) -> dict:
        """List published component sets in a file."""
        return self._get(f"/files/{file_key}/component_sets")

    def get_file_styles(self, file_key: str) -> dict:
        """List published styles in a file."""
        return self._get(f"/files/{file_key}/styles")

    def get_team_components(self, team_id: str, page_size: int = 30, cursor: str | None = None) -> dict:
        """List team library components."""
        params: dict[str, Any] = {"page_size": page_size}
        if cursor:
            params["after"] = cursor
        return self._get(f"/teams/{team_id}/components", params=params)

    def get_team_component_sets(self, team_id: str, page_size: int = 30, cursor: str | None = None) -> dict:
        """List team library component sets."""
        params: dict[str, Any] = {"page_size": page_size}
        if cursor:
            params["after"] = cursor
        return self._get(f"/teams/{team_id}/component_sets", params=params)

    def get_team_styles(self, team_id: str, page_size: int = 30, cursor: str | None = None) -> dict:
        """List team library styles."""
        params: dict[str, Any] = {"page_size": page_size}
        if cursor:
            params["after"] = cursor
        return self._get(f"/teams/{team_id}/styles", params=params)

    def get_component(self, component_key: str) -> dict:
        """Get a single component by key."""
        return self._get(f"/components/{component_key}")

    def get_component_set(self, component_set_key: str) -> dict:
        """Get a single component set by key."""
        return self._get(f"/component_sets/{component_set_key}")

    def get_style(self, style_key: str) -> dict:
        """Get a single style by key."""
        return self._get(f"/styles/{style_key}")

    # ── Projects ─────────────────────────────────────────────

    def get_team_projects(self, team_id: str) -> dict:
        """List projects in a team."""
        return self._get(f"/teams/{team_id}/projects")

    def get_project_files(self, project_id: str, branch_data: bool = False) -> dict:
        """List files in a project."""
        params = {}
        if branch_data:
            params["branch_data"] = "true"
        return self._get(f"/projects/{project_id}/files", params=params)

    # ── Versions ─────────────────────────────────────────────

    def get_file_versions(self, file_key: str) -> dict:
        """List version history of a file."""
        return self._get(f"/files/{file_key}/versions")

    # ── Variables ─────────────────────────────────────────────

    def get_local_variables(self, file_key: str) -> dict:
        """Get local variables and their collections."""
        return self._get(f"/files/{file_key}/variables/local")

    def get_published_variables(self, file_key: str) -> dict:
        """Get published variables and their collections."""
        return self._get(f"/files/{file_key}/variables/published")

    # ── Webhooks ─────────────────────────────────────────────

    def get_team_webhooks(self, team_id: str) -> dict:
        """List webhooks for a team."""
        return self._get(f"/webhooks/team/{team_id}")

    def create_webhook(
        self,
        team_id: str,
        event_type: str,
        endpoint: str,
        passcode: str,
        description: str = "",
    ) -> dict:
        """Create a webhook."""
        payload = {
            "event_type": event_type,
            "team_id": team_id,
            "endpoint": endpoint,
            "passcode": passcode,
            "description": description,
        }
        return self._post("/webhooks", payload)

    def delete_webhook(self, webhook_id: str) -> dict:
        """Delete a webhook."""
        return self._delete(f"/webhooks/{webhook_id}")

    # ── Dev Resources ────────────────────────────────────────

    def get_dev_resources(self, file_key: str, node_id: str | None = None) -> dict:
        """Get dev resources attached to a file or node."""
        params = {}
        if node_id:
            params["node_id"] = node_id
        return self._get(f"/files/{file_key}/dev_resources", params=params)
