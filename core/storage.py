"""Storage backend: local filesystem or GitHub API for persistence on Streamlit Cloud."""

import base64
import json
import os
from pathlib import Path
from typing import Dict, Optional

import requests
import streamlit as st

# Detect if we should use GitHub API (production) or local filesystem (dev)
try:
    _GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
except (KeyError, FileNotFoundError):
    _GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

try:
    _GITHUB_REPO = st.secrets["GITHUB_REPO"]
except (KeyError, FileNotFoundError):
    _GITHUB_REPO = os.getenv("GITHUB_REPO", "")

try:
    _GITHUB_BRANCH = st.secrets["GITHUB_BRANCH"]
except (KeyError, FileNotFoundError):
    _GITHUB_BRANCH = os.getenv("GITHUB_BRANCH", "main")

USE_GITHUB = bool(_GITHUB_TOKEN and _GITHUB_REPO)

_API_BASE = "https://api.github.com"
_DATA_DIR = Path("data")


def _github_headers() -> Dict[str, str]:
    return {
        "Authorization": f"token {_GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }


def _get_file_sha(filepath: str) -> Optional[str]:
    """Get the current SHA of a file in the repo (needed for updates)."""
    url = f"{_API_BASE}/repos/{_GITHUB_REPO}/contents/{filepath}"
    params = {"ref": _GITHUB_BRANCH}
    resp = requests.get(url, headers=_github_headers(), params=params, timeout=15)
    if resp.status_code == 200:
        return resp.json().get("sha")
    return None


def read_json(filename: str) -> Dict:
    """Read a JSON file from data/ directory."""
    if USE_GITHUB:
        return _github_read(f"data/{filename}")
    # Local filesystem
    filepath = _DATA_DIR / filename
    if filepath.exists():
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def write_json(filename: str, data: Dict) -> None:
    """Write a JSON file to data/ directory."""
    if USE_GITHUB:
        _github_write(f"data/{filename}", data)
    else:
        # Local filesystem
        _DATA_DIR.mkdir(exist_ok=True)
        filepath = _DATA_DIR / filename
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


def _github_read(filepath: str) -> Dict:
    """Read a JSON file from GitHub repo."""
    url = f"{_API_BASE}/repos/{_GITHUB_REPO}/contents/{filepath}"
    params = {"ref": _GITHUB_BRANCH}
    resp = requests.get(url, headers=_github_headers(), params=params, timeout=15)
    if resp.status_code == 200:
        content_b64 = resp.json().get("content", "")
        content = base64.b64decode(content_b64).decode("utf-8")
        return json.loads(content) if content.strip() else {}
    return {}


def _github_write(filepath: str, data: Dict) -> None:
    """Write a JSON file to GitHub repo (creates or updates)."""
    url = f"{_API_BASE}/repos/{_GITHUB_REPO}/contents/{filepath}"
    content = json.dumps(data, ensure_ascii=False, indent=2)
    content_b64 = base64.b64encode(content.encode("utf-8")).decode("utf-8")

    body = {
        "message": f"Auto-update {filepath}",
        "content": content_b64,
        "branch": _GITHUB_BRANCH,
    }

    # Get SHA if file exists (required for updates)
    sha = _get_file_sha(filepath)
    if sha:
        body["sha"] = sha

    resp = requests.put(url, headers=_github_headers(), json=body, timeout=15)
    resp.raise_for_status()
