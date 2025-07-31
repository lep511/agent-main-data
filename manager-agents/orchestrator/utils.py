from pathlib import Path
from typing import List
from orchestrator.orchestrator_core import AgentCategory, AgentsOverview

def collect_agent_specializations(root_dir: Path) -> AgentsOverview:
    cats: List[AgentCategory] = []

    for directory in sorted(root_dir.iterdir()):
        if not directory.is_dir():
            continue

        # gather all .md files (dropping the .md)
        specs = sorted(filepath.stem for filepath in directory.glob("*.md"))

        # Skip empty categories:
        if not specs:
            # no .md files -> move along
            continue

        # "engineering" → "Engineering"
        title = directory.name.replace("-", " ").title()
        cats.append(AgentCategory(name=title, specializations=specs))

    return AgentsOverview(categories=cats)


def get_categories_agents(overview: AgentsOverview) -> str:
    """
    Build and return the overview string for available agent categories and their specializations.
    """
    lines = []
    for cat in overview.categories:
        specs_line = "\n- ".join(cat.specializations)
        lines.append(f"\n### {cat.name}\n- {specs_line}")
    return "\n".join(lines)

def get_categories(overview: AgentsOverview) -> str:
    """
    Generate a string representing the categories of agents based on their categories.
    """
    seen: Set[str] = set()

    for cat in overview.categories:
        # Add the category name
        seen.add(cat.name.lower())

    return "|".join(seen)
