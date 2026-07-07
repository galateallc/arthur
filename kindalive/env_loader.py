"""Lightweight .env file loader — no external dependencies.

Kindalive's convention is that users put API keys in a gitignored ``.env``
file at the project root. The terminal UIs and ``kindalive.live`` expect
users to ``source .env`` manually, but the web UI is launched directly
via ``python3 -m kindalive.expression.web_ui`` and needs to pick those
keys up itself — IDEs and browser launchers do not inherit a shell's
``source`` state.

This helper parses a ``.env`` file with the same syntax the project
already uses in ``.env.example``::

    # Comment
    export ANTHROPIC_API_KEY=sk-ant-...
    OPENWEATHERMAP_API_KEY="abc 123"

Rules:

- Blank lines and lines starting with ``#`` are ignored.
- A leading ``export`` keyword is stripped.
- Values may be unquoted, single-quoted, or double-quoted.
- Inline comments after an unquoted value (``KEY=value  # note``) are stripped.
- Variables already present in ``os.environ`` are NOT overwritten, so an
  explicit shell ``export`` always wins over the file.
"""

from __future__ import annotations

import os
from pathlib import Path


def find_env_file(start: Path | None = None) -> Path | None:
    """Walk upward from ``start`` (default: cwd) looking for a ``.env`` file.

    Returns the first match, or ``None`` if no ``.env`` is found before
    hitting the filesystem root. Also checks the parent of the kindalive
    package itself so running from anywhere in a checkout still works.
    """
    candidates: list[Path] = []
    cur = (start or Path.cwd()).resolve()
    while True:
        candidates.append(cur / ".env")
        if cur.parent == cur:
            break
        cur = cur.parent
    # Also try the repo root relative to this file (two levels up from
    # kindalive/env_loader.py -> kindalive/ -> repo root).
    repo_root = Path(__file__).resolve().parent.parent
    candidates.append(repo_root / ".env")

    for path in candidates:
        if path.is_file():
            return path
    return None


def parse_env_file(path: Path) -> dict[str, str]:
    """Parse a ``.env`` file into a dict. Does not touch ``os.environ``."""
    result: dict[str, str] = {}
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].lstrip()
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        # Handle quoted values (strip matching quotes, leave content intact)
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        else:
            # Strip inline comment from unquoted values
            hash_idx = value.find("#")
            if hash_idx != -1:
                value = value[:hash_idx].rstrip()
        result[key] = value
    return result


def load_dotenv(start: Path | None = None, override: bool = False) -> Path | None:
    """Load a ``.env`` file into ``os.environ`` if one can be found.

    Returns the path that was loaded, or ``None`` if no ``.env`` was found.
    Pre-existing environment variables are preserved unless ``override``
    is True.
    """
    path = find_env_file(start)
    if path is None:
        return None
    for key, value in parse_env_file(path).items():
        if override or key not in os.environ:
            os.environ[key] = value
    return path
