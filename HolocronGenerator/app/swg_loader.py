from __future__ import annotations

import os
from typing import Dict, List

from .dtii_reader import parse_dt_iff
from .stf_reader import read_stf
from .stf_writer import calculate_crc_swg
from .model import HolocronCategory, HolocronProject, PageNode, PageLink, PageImage
from .link_tools import extract_token


def _ensure_readable(path: str) -> None:
    try:
        with open(path, "rb"):
            pass
    except OSError as e:
        raise RuntimeError(
            f"Cannot read '{path}'. The game may be running or the file is locked. Close the game and try again."
        ) from e


def _load_category_paths(filelist_path: str) -> List[str]:
    with open(filelist_path, "rb") as f:
        data = f.read()
    table = parse_dt_iff(data)
    categories: List[str] = []
    for row in table.rows:
        if not row:
            continue
        name = str(row[0]).strip()
        if name:
            categories.append(name)
    return categories


def _resolve_text(
    value: str,
    map_by_key: Dict[str, str],
    map_by_crc: Dict[int, str],
    fallback_token: str,
    resolver,
) -> str:
    token = extract_token(value)
    if token and "@" in value:
        resolved = resolver(value)
        if resolved:
            return resolved
    if token:
        if token in map_by_key:
            return map_by_key.get(token, "")
        return map_by_crc.get(calculate_crc_swg(token), "")
    return map_by_crc.get(calculate_crc_swg(fallback_token), "")


def _build_nodes_from_rows(
    rows: List[Dict[str, str]],
    name_by_key: Dict[str, str],
    name_by_crc: Dict[int, str],
    desc_by_key: Dict[str, str],
    desc_by_crc: Dict[int, str],
    resolver,
) -> List[PageNode]:
    nodes_by_path: Dict[str, PageNode] = {}
    roots: List[PageNode] = []

    for r in rows:
        if r.get("Type") != "Page":
            continue
        short_name = str(r.get("Name", "")).strip()
        parent = str(r.get("Parent", "")).strip()
        if not short_name:
            continue

        full_path = short_name if not parent else f"{parent}.{short_name}"

        data1 = str(r.get("Data1", "")).strip()
        data2 = str(r.get("Data2", "")).strip()
        title = _resolve_text(data1, name_by_key, name_by_crc, short_name, resolver)
        content = _resolve_text(data2, desc_by_key, desc_by_crc, short_name, resolver)

        node = PageNode(
            short_name=short_name,
            title=title,
            content=content,
            title_token=data1,
            content_token=data2,
        )
        nodes_by_path[full_path] = node

    for r in rows:
        if r.get("Type") != "Page":
            continue
        short_name = str(r.get("Name", "")).strip()
        parent = str(r.get("Parent", "")).strip()
        if not short_name:
            continue
        full_path = short_name if not parent else f"{parent}.{short_name}"
        node = nodes_by_path.get(full_path)
        if node is None:
            continue
        if not parent:
            roots.append(node)
        else:
            parent_node = nodes_by_path.get(parent)
            if parent_node is None:
                parent_node = PageNode(short_name=parent.split(".")[-1], title="", content="")
                nodes_by_path[parent] = parent_node
                roots.append(parent_node)
            parent_node.add_child(node)

    for r in rows:
        if r.get("Type") != "String":
            continue
        parent = str(r.get("Parent", "")).strip()
        if not parent:
            continue
        node = nodes_by_path.get(parent)
        if node is None:
            continue
        data1 = str(r.get("Data1", "")).strip()
        text = _resolve_text(data1, desc_by_key, desc_by_crc, node.short_name, resolver)
        if text:
            node.content = f"{node.content}\n\n{text}".strip() if node.content else text
        if data1 and not node.content_token:
            node.content_token = data1

    for r in rows:
        if r.get("Type") != "Image":
            continue
        parent = str(r.get("Parent", "")).strip()
        if not parent:
            continue
        node = nodes_by_path.get(parent)
        if node is None:
            continue
        resource = str(r.get("Data1", "")).strip()
        name = str(r.get("Name", "")).strip()
        if resource:
            node.add_image(PageImage(resource=resource, name=name))

    for r in rows:
        if r.get("Type") != "LinkButton":
            continue
        parent = str(r.get("Parent", "")).strip()
        if not parent:
            continue
        node = nodes_by_path.get(parent)
        if node is None:
            continue
        data1 = str(r.get("Data1", "")).strip()
        label = _resolve_text(data1, desc_by_key, desc_by_crc, node.short_name, resolver)
        target = str(r.get("Data2", "")).strip()
        key = extract_token(data1)
        name = str(r.get("Name", "")).strip()
        if label and target:
            node.add_link(PageLink(label=label, target=target, key=key, name=name, label_token=data1))

    return roots


def load_project_from_swg(root: str, language: str = "en") -> HolocronProject:
    filelist_path = os.path.join(root, "datatables", "knowledgebase", "filelist.iff")
    if not os.path.exists(filelist_path):
        raise FileNotFoundError("filelist.iff not found in datatables/knowledgebase")

    _ensure_readable(filelist_path)
    categories = _load_category_paths(filelist_path)
    project = HolocronProject()

    stf_cache: Dict[str, Dict[str, Dict]] = {}

    def _get_stf_maps(stf_path: str) -> tuple[Dict[str, str], Dict[int, str]]:
        if stf_path in stf_cache:
            entry = stf_cache[stf_path]
        else:
            entry = {"by_key": {}, "by_crc": {}, "entries": [], "tokens": []}
            stf_cache[stf_path] = entry
        if not entry["entries"] and os.path.exists(stf_path):
            _ensure_readable(stf_path)
            stf = read_stf(stf_path)
            entry["by_key"] = stf.map_by_key()
            entry["by_crc"] = stf.map_by_crc()
            entry["entries"] = stf.entries
        if not entry["by_key"] and entry["entries"] and entry["tokens"]:
            tokens = []
            seen = set()
            for t in entry["tokens"]:
                if t and t not in seen:
                    tokens.append(t)
                    seen.add(t)
            entries_sorted = sorted(entry["entries"], key=lambda e: e.string_id)
            if len(tokens) >= len(entries_sorted):
                entry["by_key"] = {t: e.text for t, e in zip(tokens, entries_sorted)}
        return entry["by_key"], entry["by_crc"]

    def _resolver(value: str) -> str:
        val = value or ""
        if not val.startswith("@") or ":" not in val:
            return ""
        token = val.split(":", 1)[1].strip()
        if val.startswith("@kb/"):
            part = val.split("@kb/", 1)[1].split(":", 1)[0]
            stf_path = os.path.join(root, "string", language, "kb", f"{part}.stf")
        else:
            part = val[1:].split(":", 1)[0]
            stf_path = os.path.join(root, "string", language, f"{part}.stf")
        if stf_path not in stf_cache:
            stf_cache[stf_path] = {"by_key": {}, "by_crc": {}, "entries": [], "tokens": []}
        if token:
            stf_cache[stf_path]["tokens"].append(token)
        by_key, by_crc = _get_stf_maps(stf_path)
        if token in by_key:
            return by_key.get(token, "")
        return by_crc.get(calculate_crc_swg(token), "")

    for cat in categories:
        cat_name = cat
        dt_filename = cat
        if cat.lower().endswith(".iff"):
            cat_name = cat[:-4]
            dt_filename = cat
        else:
            dt_filename = f"{cat}.iff"

        dt_path = os.path.join(root, "datatables", "knowledgebase", dt_filename)
        if not os.path.exists(dt_path):
            continue

        _ensure_readable(dt_path)
        with open(dt_path, "rb") as f:
            dt = parse_dt_iff(f.read())

        rows: List[Dict[str, str]] = []
        col_names = [c.name for c in dt.columns]
        for row in dt.rows:
            record: Dict[str, str] = {}
            for i, col in enumerate(col_names):
                record[col] = str(row[i]) if i < len(row) else ""
            rows.append(record)

        stf_base = None
        for r in rows:
            for key in ("Data1", "Data2"):
                val = str(r.get(key, ""))
                if "@kb/" in val and ":" in val:
                    part = val.split("@kb/", 1)[1].split(":", 1)[0]
                    if part.endswith("_n"):
                        stf_base = part[:-2]
                        break
                    if part.endswith("_d"):
                        stf_base = part[:-2]
                        break
            if stf_base:
                break
        if not stf_base:
            stf_base = f"kb_{cat_name}"

        name_path = os.path.join(root, "string", language, "kb", f"{stf_base}_n.stf")
        desc_path = os.path.join(root, "string", language, "kb", f"{stf_base}_d.stf")

        name_by_key, name_by_crc = _get_stf_maps(name_path)
        desc_by_key, desc_by_crc = _get_stf_maps(desc_path)

        roots = _build_nodes_from_rows(rows, name_by_key, name_by_crc, desc_by_key, desc_by_crc, _resolver)
        category = HolocronCategory(name=cat_name)
        for root_node in roots:
            category.add_root(root_node)
        project.add_category(category)

    return project
