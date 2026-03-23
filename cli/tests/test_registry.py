from pathlib import Path
from ait.core.registry import Resource, scan_resources, find_resource

import pytest


@pytest.fixture
def sample_repo(tmp_path: Path) -> Path:
    """Create a minimal repo structure with sample resources."""
    # claude rule
    rules_dir = tmp_path / "rules" / "claude"
    rules_dir.mkdir(parents=True)
    (rules_dir / "test-rule.md").write_text(
        "---\nname: test-rule\ndescription: A test rule\ntype: claude-rule\n"
        "tags: [test]\nversion: 1.0.0\nauthor: tester\n---\n\nRule content here.\n"
    )

    # skill
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    (skills_dir / "test-skill.md").write_text(
        "---\nname: test-skill\ndescription: A test skill\ntype: skill\n"
        "tags: [test, ai]\nversion: 0.1.0\nauthor: tester\n---\n\nSkill content.\n"
    )

    # mcp
    mcp_dir = tmp_path / "mcp"
    mcp_dir.mkdir()
    (mcp_dir / "test-mcp.json").write_text(
        '{"_meta": {"name": "test-mcp", "description": "Test MCP", "type": "mcp",'
        ' "tags": ["test"], "version": "1.0.0", "author": "tester"},'
        ' "mcpServers": {"test": {"command": "echo"}}}'
    )

    # template
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    (templates_dir / "test-tmpl.md").write_text(
        "---\nname: test-tmpl\ndescription: A test template\ntype: template\n"
        "tags: [test]\nversion: 1.0.0\nauthor: tester\n---\n\nTemplate content.\n"
    )

    return tmp_path


def test_scan_resources_finds_all_types(sample_repo: Path) -> None:
    resources = scan_resources(sample_repo)
    names = {r.name for r in resources}
    assert names == {"test-rule", "test-skill", "test-mcp", "test-tmpl"}


def test_scan_resources_parses_metadata(sample_repo: Path) -> None:
    resources = scan_resources(sample_repo)
    rule = next(r for r in resources if r.name == "test-rule")
    assert rule.type == "claude-rule"
    assert rule.tags == ["test"]
    assert rule.version == "1.0.0"
    assert rule.author == "tester"
    assert rule.description == "A test rule"
    assert rule.file_path == sample_repo / "rules" / "claude" / "test-rule.md"


def test_scan_resources_skips_gitkeep(sample_repo: Path) -> None:
    (sample_repo / "rules" / "claude" / ".gitkeep").touch()
    resources = scan_resources(sample_repo)
    names = {r.name for r in resources}
    assert ".gitkeep" not in names


def test_find_resource_by_name(sample_repo: Path) -> None:
    resources = scan_resources(sample_repo)
    result = find_resource(resources, "test-skill")
    assert result is not None
    assert result.type == "skill"


def test_find_resource_not_found(sample_repo: Path) -> None:
    resources = scan_resources(sample_repo)
    result = find_resource(resources, "nonexistent")
    assert result is None


def test_scan_resources_filters_by_type(sample_repo: Path) -> None:
    resources = scan_resources(sample_repo, type_filter="claude-rule")
    assert len(resources) == 1
    assert resources[0].name == "test-rule"


def test_scan_resources_filters_by_tag(sample_repo: Path) -> None:
    resources = scan_resources(sample_repo, tag_filter="ai")
    assert len(resources) == 1
    assert resources[0].name == "test-skill"
