import json
from pathlib import Path

import pytest

from ait.core.linker import create_symlink, copy_file, merge_mcp, remove_symlink, remove_mcp_keys


@pytest.fixture
def source_file(tmp_path: Path) -> Path:
    src = tmp_path / "source" / "test.md"
    src.parent.mkdir()
    src.write_text("content")
    return src


def test_create_symlink(source_file: Path, tmp_path: Path) -> None:
    target = tmp_path / "target" / "test.md"
    create_symlink(source_file, target)
    assert target.is_symlink()
    assert target.resolve() == source_file.resolve()


def test_create_symlink_creates_parent_dirs(source_file: Path, tmp_path: Path) -> None:
    target = tmp_path / "deep" / "nested" / "test.md"
    create_symlink(source_file, target)
    assert target.is_symlink()


def test_create_symlink_replaces_existing(source_file: Path, tmp_path: Path) -> None:
    target = tmp_path / "target" / "test.md"
    target.parent.mkdir(parents=True)
    target.write_text("old")
    create_symlink(source_file, target)
    assert target.is_symlink()


def test_copy_file(source_file: Path, tmp_path: Path) -> None:
    target = tmp_path / "target" / "copy.md"
    copy_file(source_file, target)
    assert target.read_text() == "content"
    assert not target.is_symlink()


def test_copy_file_does_not_overwrite_without_force(source_file: Path, tmp_path: Path) -> None:
    target = tmp_path / "target" / "copy.md"
    target.parent.mkdir(parents=True)
    target.write_text("existing")
    was_copied = copy_file(source_file, target, force=False)
    assert not was_copied
    assert target.read_text() == "existing"


def test_copy_file_overwrites_with_force(source_file: Path, tmp_path: Path) -> None:
    target = tmp_path / "target" / "copy.md"
    target.parent.mkdir(parents=True)
    target.write_text("existing")
    was_copied = copy_file(source_file, target, force=True)
    assert was_copied
    assert target.read_text() == "content"


def test_copy_file_strips_frontmatter(tmp_path: Path) -> None:
    source = tmp_path / "source" / "tmpl.md"
    source.parent.mkdir()
    source.write_text("---\nname: test\ntype: template\n---\n\nActual content here.\n")
    target = tmp_path / "target" / "CLAUDE.md"
    was_copied = copy_file(source, target, strip_frontmatter=True)
    assert was_copied
    content = target.read_text()
    assert "---" not in content
    assert "Actual content here." in content


def test_merge_mcp_creates_new(tmp_path: Path) -> None:
    mcp_source = {"mcpServers": {"ctx7": {"command": "npx", "args": ["-y", "ctx7"]}}}
    target = tmp_path / ".claude" / "mcp.json"
    keys = merge_mcp(mcp_source, target)
    assert keys == ["ctx7"]
    result = json.loads(target.read_text())
    assert "ctx7" in result["mcpServers"]


def test_merge_mcp_preserves_existing(tmp_path: Path) -> None:
    target = tmp_path / ".claude" / "mcp.json"
    target.parent.mkdir(parents=True)
    target.write_text(json.dumps({"mcpServers": {"existing": {"command": "echo"}}}))

    mcp_source = {"mcpServers": {"new-server": {"command": "npx"}}}
    keys = merge_mcp(mcp_source, target)
    assert keys == ["new-server"]
    result = json.loads(target.read_text())
    assert "existing" in result["mcpServers"]
    assert "new-server" in result["mcpServers"]


def test_merge_mcp_does_not_overwrite_existing_key(tmp_path: Path) -> None:
    target = tmp_path / ".claude" / "mcp.json"
    target.parent.mkdir(parents=True)
    target.write_text(json.dumps({"mcpServers": {"ctx7": {"command": "old"}}}))

    mcp_source = {"mcpServers": {"ctx7": {"command": "new"}}}
    keys = merge_mcp(mcp_source, target)
    assert keys == []
    result = json.loads(target.read_text())
    assert result["mcpServers"]["ctx7"]["command"] == "old"


def test_remove_symlink(source_file: Path, tmp_path: Path) -> None:
    target = tmp_path / "target" / "test.md"
    create_symlink(source_file, target)
    remove_symlink(target)
    assert not target.exists()


def test_remove_mcp_keys(tmp_path: Path) -> None:
    target = tmp_path / "mcp.json"
    target.write_text(json.dumps({"mcpServers": {"keep": {"command": "a"}, "remove": {"command": "b"}}}))
    remove_mcp_keys(target, ["remove"])
    result = json.loads(target.read_text())
    assert "keep" in result["mcpServers"]
    assert "remove" not in result["mcpServers"]
