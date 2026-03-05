from __future__ import annotations

from typing import List

from .model import HolocronCategory, PageNode


def _siblings(category: HolocronCategory, node: PageNode) -> List[PageNode]:
    if node.parent is None:
        return category.root_pages
    return node.parent.children


def move_node_up(category: HolocronCategory, node: PageNode) -> bool:
    siblings = _siblings(category, node)
    try:
        idx = siblings.index(node)
    except ValueError:
        return False
    if idx <= 0:
        return False
    siblings[idx - 1], siblings[idx] = siblings[idx], siblings[idx - 1]
    return True


def move_node_down(category: HolocronCategory, node: PageNode) -> bool:
    siblings = _siblings(category, node)
    try:
        idx = siblings.index(node)
    except ValueError:
        return False
    if idx >= len(siblings) - 1:
        return False
    siblings[idx + 1], siblings[idx] = siblings[idx], siblings[idx + 1]
    return True
