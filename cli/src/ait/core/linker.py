from __future__ import annotations

import json
import shutil
from pathlib import Path


def create_symlink(source: Path, target: Path) -> None:
    """Create a symlink from target -> source. Creates parent dirs, replaces existing."""
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() or target.is_symlink():
        target.unlink()
    target.symlink_to(source.resolve())


def copy_file(source: Path, target: Path, *, force: bool = False, strip_frontmatter: bool = False) -> bool:
    """Copy source to target. Returns False if target exists and force=False.

    If strip_frontmatter=True, removes YAML frontmatter (---...---) from markdown files.
    """
    if target.exists() and not force:
        return False
    target.parent.mkdir(parents=True, exist_ok=True)
    if strip_frontmatter:
        import frontmatter
        post = frontmatter.load(str(source))
        target.write_text(post.content, encoding="utf-8")
    else:
        shutil.copy2(source, target)
    return True


def merge_mcp(mcp_source: dict, target: Path) -> list[str]:
    """Merge mcpServers into target mcp.json. Returns list of newly added keys.

    Existing keys are NOT overwritten.
    """
    target.parent.mkdir(parents=True, exist_ok=True)

    if target.exists():
        existing = json.loads(target.read_text(encoding="utf-8"))
    else:
        existing = {"mcpServers": {}}

    if "mcpServers" not in existing:
        existing["mcpServers"] = {}

    source_servers = mcp_source.get("mcpServers", {})
    added_keys: list[str] = []
    for key, value in source_servers.items():
        if key not in existing["mcpServers"]:
            existing["mcpServers"][key] = value
            added_keys.append(key)

    target.write_text(json.dumps(existing, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return added_keys


def remove_symlink(target: Path) -> bool:
    """Remove a symlink. Returns True if removed."""
    if target.is_symlink() or target.exists():
        target.unlink()
        return True
    return False


def remove_mcp_keys(target: Path, keys: list[str]) -> None:
    """Remove specific mcpServer keys from mcp.json."""
    if not target.exists():
        return
    data = json.loads(target.read_text(encoding="utf-8"))
    servers = data.get("mcpServers", {})
    for key in keys:
        servers.pop(key, None)
    target.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
