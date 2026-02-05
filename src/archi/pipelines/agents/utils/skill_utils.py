"""
Utility for loading skill files that provide domain-specific knowledge to agent tools.

Skills are markdown files stored in a configurable subdirectory (default: ``skills/``)
alongside the agent's configuration file.  They are appended to tool descriptions so
the LLM has context about field names, query patterns, and domain conventions.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from src.utils.logging import get_logger

logger = get_logger(__name__)


def load_skill(skill_name: str, config: Dict[str, Any]) -> Optional[str]:
    """
    Load a skill markdown file by name from the configured skills directory.

    Skills are markdown files stored in a directory specified by ``skills_dir``
    in the config (relative to config_path), defaulting to ``skills/`` if not specified.
    Returns ``None`` if the skill file doesn't exist or cannot be read.

    Args:
        skill_name: Name of the skill file (without .md extension).
        config: Agent config dict (automatically contains ``config_path`` and optionally ``skills_dir``).

    Returns:
        Skill content as string, or ``None`` if not found.
    """
    config_path = config.get("config_path")
    if not config_path:
        logger.warning("No config_path in config; cannot load skill '%s'", skill_name)
        return None

    # Allow configurable skills directory, default to "skills"
    skills_dir = config.get("skills_dir", "skills")
    skill_path = Path(config_path).parent / skills_dir / f"{skill_name}.md"
    if not skill_path.exists():
        logger.warning("Skill file not found: %s", skill_path)
        return None

    try:
        content = skill_path.read_text(encoding="utf-8")
        logger.info("Loaded skill '%s' from %s (%d chars)", skill_name, skill_path, len(content))
        return content
    except Exception as e:
        logger.error("Failed to read skill file %s: %s", skill_path, e)
        return None
