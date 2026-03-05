from __future__ import annotations

from typing import Any, Dict, List
import json

from .model import HolocronProject, HolocronCategory, PageNode, PageLink, PageImage

SCHEMA_ID = "holocron-gen-tool/v3"


def _link_to_dict(link: PageLink) -> Dict[str, Any]:
    return {
        "label": link.label,
        "target": link.target,
        "key": link.key,
        "name": link.name,
        "label_token": link.label_token,
    }


def _image_to_dict(image: PageImage) -> Dict[str, Any]:
    return {
        "resource": image.resource,
        "name": image.name,
    }


def _page_to_dict(node: PageNode) -> Dict[str, Any]:
    return {
        "short_name": node.short_name,
        "title": node.title,
        "content": node.content,
        "title_token": node.title_token,
        "content_token": node.content_token,
        "links": [_link_to_dict(l) for l in node.links],
        "images": [_image_to_dict(i) for i in node.images],
        "children": [_page_to_dict(c) for c in node.children],
    }


def project_to_dict(project: HolocronProject) -> Dict[str, Any]:
    return {
        "schema": SCHEMA_ID,
        "categories": [
            {
                "name": cat.name,
                "pages": [_page_to_dict(p) for p in cat.root_pages],
            }
            for cat in project.categories
        ],
    }


def _link_from_dict(data: Dict[str, Any]) -> PageLink:
    return PageLink(
        label=str(data.get("label", "")),
        target=str(data.get("target", "")),
        key=str(data.get("key", "")),
        name=str(data.get("name", "")),
        label_token=str(data.get("label_token", "")),
    )


def _image_from_dict(data: Dict[str, Any]) -> PageImage:
    return PageImage(
        resource=str(data.get("resource", "")),
        name=str(data.get("name", "")),
    )


def _page_from_dict(data: Dict[str, Any]) -> PageNode:
    node = PageNode(
        short_name=str(data.get("short_name", "")),
        title=str(data.get("title", "")),
        content=str(data.get("content", "")),
        title_token=str(data.get("title_token", "")),
        content_token=str(data.get("content_token", "")),
    )
    for link in data.get("links", []) or []:
        node.add_link(_link_from_dict(link))
    for image in data.get("images", []) or []:
        node.add_image(_image_from_dict(image))
    for child in data.get("children", []) or []:
        child_node = _page_from_dict(child)
        node.add_child(child_node)
    return node


def project_from_dict(data: Dict[str, Any]) -> HolocronProject:
    project = HolocronProject()
    for cat_data in data.get("categories", []) or []:
        name = str(cat_data.get("name", ""))
        category = HolocronCategory(name=name)
        for page_data in cat_data.get("pages", []) or []:
            page = _page_from_dict(page_data)
            category.add_root(page)
        project.add_category(category)
    return project


def save_project(path: str, project: HolocronProject) -> None:
    payload = project_to_dict(project)
    text = json.dumps(payload, indent=2, ensure_ascii=False)
    text = text.replace("\n", "\r\n")
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)


def load_project(path: str) -> HolocronProject:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("Invalid project file")
    return project_from_dict(data)
