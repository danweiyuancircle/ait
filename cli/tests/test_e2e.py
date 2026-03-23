"""End-to-end test using a temporary repo structure."""
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from ait.main import app

runner = CliRunner()


@pytest.fixture
def mock_repo(tmp_path: Path) -> Path:
    """Create a complete mock repo."""
    # Claude rule
    (tmp_path / "rules" / "claude").mkdir(parents=True)
    (tmp_path / "rules" / "claude" / "test-rule.md").write_text(
        "---\nname: test-rule\ndescription: Test\ntype: claude-rule\n"
        "tags: [test]\nversion: 1.0.0\nauthor: tester\n---\nContent\n"
    )

    # Cursor rule
    (tmp_path / "rules" / "cursor").mkdir(parents=True)
    (tmp_path / "rules" / "cursor" / "test-cursor.mdc").write_text(
        "---\nname: test-cursor\ndescription: Cursor rule\ntype: cursor-rule\n"
        "tags: [test]\nversion: 1.0.0\nauthor: tester\nalwaysApply: true\n---\nCursor content\n"
    )

    # Skill
    (tmp_path / "skills").mkdir()
    (tmp_path / "skills" / "test-skill.md").write_text(
        "---\nname: test-skill\ndescription: Skill\ntype: skill\n"
        "tags: [test]\nversion: 1.0.0\nauthor: tester\n---\nContent\n"
    )

    # Template
    (tmp_path / "templates").mkdir()
    (tmp_path / "templates" / "test-tmpl.md").write_text(
        "---\nname: test-tmpl\ndescription: Template\ntype: template\n"
        "tags: [test]\nversion: 1.0.0\nauthor: tester\n---\nTemplate content\n"
    )

    # MCP
    (tmp_path / "mcp").mkdir()
    (tmp_path / "mcp" / "test-mcp.json").write_text(json.dumps({
        "_meta": {"name": "test-mcp", "description": "MCP", "type": "mcp",
                  "tags": ["test"], "version": "1.0.0", "author": "tester"},
        "mcpServers": {"test-server": {"command": "echo"}}
    }))

    # Profile
    (tmp_path / "profiles").mkdir()
    (tmp_path / "profiles" / "test-profile.yaml").write_text(
        "name: test-profile\ndescription: Test profile\nauthor: tester\nversion: 1.0.0\n\n"
        "rules:\n  claude:\n    - test-rule\n\nskills:\n  - test-skill\n\n"
        "templates:\n  - test-tmpl\n\nmcp:\n  - test-mcp\n"
    )

    return tmp_path


def test_list(mock_repo: Path) -> None:
    result = runner.invoke(app, ["list", "--repo-path", str(mock_repo)])
    assert result.exit_code == 0
    assert "test-rule" in result.output


def test_show(mock_repo: Path) -> None:
    result = runner.invoke(app, ["show", "test-rule", "--repo-path", str(mock_repo)])
    assert result.exit_code == 0
    assert "test-rule" in result.output


def test_profiles(mock_repo: Path) -> None:
    result = runner.invoke(app, ["profiles", "--repo-path", str(mock_repo)])
    assert result.exit_code == 0
    assert "test-profile" in result.output


def test_use_creates_resources(mock_repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    monkeypatch.chdir(project_dir)

    result = runner.invoke(app, ["use", "test-profile", "--repo-path", str(mock_repo), "--force"])
    assert result.exit_code == 0

    # Check symlinks
    assert (project_dir / ".claude" / "rules" / "test-rule.md").is_symlink()
    assert (project_dir / ".claude" / "skills" / "test-skill.md").is_symlink()

    # Check template was copied
    assert (project_dir / "CLAUDE.md").exists()
    assert not (project_dir / "CLAUDE.md").is_symlink()

    # Check MCP was merged
    mcp = json.loads((project_dir / ".claude" / "mcp.json").read_text())
    assert "test-server" in mcp["mcpServers"]

    # Check config
    config = json.loads((project_dir / ".ai-rules.json").read_text())
    assert config["profile"] == "test-profile"
    assert len(config["resources"]) == 4


def test_use_replacement_cleans_old_resources(mock_repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Switching profiles removes resources from old profile not in new one."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    monkeypatch.chdir(project_dir)

    # Create a second profile with only a skill (no rule, no template, no mcp)
    (mock_repo / "profiles" / "minimal.yaml").write_text(
        "name: minimal\ndescription: Minimal\nauthor: tester\nversion: 1.0.0\n\n"
        "skills:\n  - test-skill\n"
    )

    # Apply full profile first
    runner.invoke(app, ["use", "test-profile", "--repo-path", str(mock_repo), "--force"])
    assert (project_dir / ".claude" / "rules" / "test-rule.md").is_symlink()
    assert (project_dir / "CLAUDE.md").exists()

    # Switch to minimal profile
    runner.invoke(app, ["use", "minimal", "--repo-path", str(mock_repo), "--force"])

    # Old resources should be cleaned up
    assert not (project_dir / ".claude" / "rules" / "test-rule.md").exists()
    assert not (project_dir / "CLAUDE.md").exists()
    # Skill should still be there
    assert (project_dir / ".claude" / "skills" / "test-skill.md").is_symlink()


def test_use_validates_template_count(mock_repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    monkeypatch.chdir(project_dir)

    # Create a profile with 2 templates
    (mock_repo / "profiles" / "bad.yaml").write_text(
        "name: bad\ndescription: Bad\nauthor: tester\nversion: 1.0.0\n\n"
        "templates:\n  - test-tmpl\n  - test-tmpl\n"
    )
    result = runner.invoke(app, ["use", "bad", "--repo-path", str(mock_repo)])
    assert result.exit_code == 1


def test_sync_rebuilds_symlinks(mock_repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    monkeypatch.chdir(project_dir)

    # Apply profile
    runner.invoke(app, ["use", "test-profile", "--repo-path", str(mock_repo), "--force"])

    # Delete a symlink to simulate broken state
    rule_link = project_dir / ".claude" / "rules" / "test-rule.md"
    rule_link.unlink()
    assert not rule_link.exists()

    # Sync should rebuild it
    result = runner.invoke(app, ["sync"])
    assert result.exit_code == 0
    assert rule_link.is_symlink()


def test_add_and_remove(mock_repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    monkeypatch.chdir(project_dir)

    # Add
    result = runner.invoke(app, ["add", "test-rule", "--repo-path", str(mock_repo)])
    assert result.exit_code == 0
    assert (project_dir / ".claude" / "rules" / "test-rule.md").is_symlink()

    # Remove
    result = runner.invoke(app, ["remove", "test-rule"])
    assert result.exit_code == 0
    assert not (project_dir / ".claude" / "rules" / "test-rule.md").exists()
