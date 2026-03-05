from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from .model import HolocronProject, HolocronCategory, PageNode


def sanitize_key(text: str) -> str:
    raw = "".join(ch for ch in (text or "").lower() if ch.isalnum() or ch == "_")
    if not raw:
        return "link"
    if not raw[0].isalpha():
        return f"link_{raw}"
    return raw


def extract_token(value: str) -> str:
    v = (value or "").strip()
    if not v or ":" not in v:
        return ""
    return v.split(":", 1)[1].strip()


def build_path_index(project: HolocronProject) -> Dict[str, List[Tuple[HolocronCategory, PageNode]]]:
    index: Dict[str, List[Tuple[HolocronCategory, PageNode]]] = {}
    for category in project.categories:
        for node in category.walk():
            path = node.full_path()
            index.setdefault(path, []).append((category, node))
    return index


def validate_link_target(project: HolocronProject, target: str) -> bool:
    target = (target or "").strip()
    if not target:
        return False
    index = build_path_index(project)
    return target in index


def find_path(
    project: HolocronProject,
    target: str,
    preferred_category: Optional[HolocronCategory] = None,
) -> Optional[Tuple[HolocronCategory, PageNode]]:
    target = (target or "").strip()
    if not target:
        return None
    index = build_path_index(project)
    matches = index.get(target, [])
    if not matches:
        return None
    if preferred_category:
        for category, node in matches:
            if category == preferred_category:
                return category, node
    return matches[0]
