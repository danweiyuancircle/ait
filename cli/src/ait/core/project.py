from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from ait.core.config import CONFIG_FILENAME


def load_project_config(project_dir: Path) -> dict | None:
    config_path = project_dir / CONFIG_FILENAME
    if config_path.exists():
        return json.loads(config_path.read_text(encoding="utf-8"))
    return None


def save_project_config(project_dir: Path, config: dict) -> None:
    config_path = project_dir / CONFIG_FILENAME
    config["updated_at"] = datetime.now(tz=timezone.utc).isoformat()
    config_path.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def ensure_gitignore(project_dir: Path) -> None:
    gitignore = project_dir / ".gitignore"
    entry = CONFIG_FILENAME
    if gitignore.exists():
        content = gitignore.read_text(encoding="utf-8")
        if entry in content.splitlines():
            return
        if not content.endswith("\n"):
            content += "\n"
        content += f"{entry}\n"
        gitignore.write_text(content, encoding="utf-8")
    else:
        gitignore.write_text(f"{entry}\n", encoding="utf-8")
