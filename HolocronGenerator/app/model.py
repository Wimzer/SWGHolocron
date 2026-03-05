from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional
import re

_SHORT_NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")


def is_valid_short_name(name: str) -> bool:
    if not name:
        return False
    return _SHORT_NAME_RE.match(name) is not None


@dataclass
class PageLink:
    label: str
    target: str
    key: str = ""
    name: str = ""
    label_token: str = ""


@dataclass
class PageImage:
    resource: str
    name: str = ""


@dataclass(eq=False)
class PageNode:
    short_name: str
    title: str
    content: str
    title_token: str = ""
    content_token: str = ""
    links: List[PageLink] = field(default_factory=list)
    images: List[PageImage] = field(default_factory=list)
    children: List[PageNode] = field(default_factory=list)
    parent: Optional[PageNode] = None

    def full_path(self) -> str:
        parts: List[str] = []
        node: Optional[PageNode] = self
        while node is not None:
            parts.append(node.short_name)
            node = node.parent
        return ".".join(reversed(parts))

    def add_child(self, child: PageNode) -> None:
        child.parent = self
        self.children.append(child)

    def remove_child(self, child: PageNode) -> None:
        if child in self.children:
            self.children.remove(child)
            child.parent = None

    def add_link(self, link: PageLink) -> None:
        self.links.append(link)

    def remove_link(self, link: PageLink) -> None:
        if link in self.links:
            self.links.remove(link)

    def add_image(self, image: PageImage) -> None:
        self.images.append(image)

    def remove_image(self, image: PageImage) -> None:
        if image in self.images:
            self.images.remove(image)

    def walk(self) -> List[PageNode]:
        nodes: List[PageNode] = [self]
        for child in self.children:
            nodes.extend(child.walk())
        return nodes


@dataclass
class HolocronCategory:
    name: str
    root_pages: List[PageNode] = field(default_factory=list)

    def add_root(self, node: PageNode) -> None:
        node.parent = None
        self.root_pages.append(node)

    def remove_root(self, node: PageNode) -> None:
        if node in self.root_pages:
            self.root_pages.remove(node)
            node.parent = None

    def walk(self) -> List[PageNode]:
        nodes: List[PageNode] = []
        for root in self.root_pages:
            nodes.extend(root.walk())
        return nodes

    def find_by_path(self, path: str) -> Optional[PageNode]:
        for node in self.walk():
            if node.full_path() == path:
                return node
        return None


@dataclass
class HolocronProject:
    categories: List[HolocronCategory] = field(default_factory=list)

    def add_category(self, category: HolocronCategory) -> None:
        self.categories.append(category)

    def remove_category(self, category: HolocronCategory) -> None:
        if category in self.categories:
            self.categories.remove(category)

    def get_category(self, name: str) -> Optional[HolocronCategory]:
        for cat in self.categories:
            if cat.name == name:
                return cat
        return None

    def category_names(self) -> List[str]:
        return [c.name for c in self.categories]
