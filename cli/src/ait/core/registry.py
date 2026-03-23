from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import frontmatter

from ait.core.config import RESOURCE_DIRS, VALID_TYPES


@dataclass
class Resource:
    name: str
    description: str
    type: str
    tags: list[str]
    version: str
    author: str
    file_path: Path
    content: str = field(repr=False, default="")


def _parse_markdown_resource(file_path: Path) -> Resource | None:
    """Parse a markdown file with YAML frontmatter."""
    post = frontmatter.load(str(file_path))
    meta = post.metadata
    if "name" not in meta or "type" not in meta:
        return None
    return Resource(
        name=meta["name"],
        description=meta.get("description", ""),
        type=meta["type"],
        tags=meta.get("tags", []),
        version=meta.get("version", "0.0.0"),
        author=meta.get("author", ""),
        file_path=file_path,
        content=post.content,
    )


def _parse_json_resource(file_path: Path) -> Resource | None:
    """Parse a JSON file with _meta block."""
    data = json.loads(file_path.read_text(encoding="utf-8"))
    meta = data.get("_meta")
    if not meta or "name" not in meta:
        return None
    return Resource(
        name=meta["name"],
        description=meta.get("description", ""),
        type=meta.get("type", "mcp"),
        tags=meta.get("tags", []),
        version=meta.get("version", "0.0.0"),
        author=meta.get("author", ""),
        file_path=file_path,
    )


def scan_resources(
    repo_path: Path,
    *,
    type_filter: str | None = None,
    tag_filter: str | None = None,
) -> list[Resource]:
    """Scan the repo and return all parsed resources."""
    resources: list[Resource] = []

    for resource_type, rel_dir in RESOURCE_DIRS.items():
        dir_path = repo_path / rel_dir
        if not dir_path.is_dir():
            continue
        for file_path in sorted(dir_path.iterdir()):
            if file_path.name.startswith("."):
                continue
            if not file_path.is_file():
                continue

            resource: Resource | None = None
            if file_path.suffix in (".md", ".mdc"):
                resource = _parse_markdown_resource(file_path)
            elif file_path.suffix == ".json":
                resource = _parse_json_resource(file_path)

            if resource and resource.type in VALID_TYPES:
                resources.append(resource)

    if type_filter:
        resources = [r for r in resources if r.type == type_filter]
    if tag_filter:
        resources = [r for r in resources if tag_filter in r.tags]

    return resources


def find_resource(resources: list[Resource], name: str) -> Resource | None:
    """Find a resource by name."""
    for r in resources:
        if r.name == name:
            return r
    return None
