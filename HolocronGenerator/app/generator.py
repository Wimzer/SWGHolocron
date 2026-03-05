from __future__ import annotations

from typing import Dict, List, Tuple, Iterable
import os

from .model import HolocronCategory, HolocronProject, PageNode, PageLink
from .link_tools import sanitize_key
from .stf_writer import StfEntry, build_entries_from_dict, write_stf
from .dtii_writer import build_kb_table, write_dt_iff, COLTYPE_STRING_V1
from .filelist import write_filelist_from_categories


def _walk_pages(pages: List[PageNode]) -> List[PageNode]:
    result: List[PageNode] = []
    for p in pages:
        result.append(p)
        if p.children:
            result.extend(_walk_pages(p.children))
    return result


def validate_unique_paths(category: HolocronCategory) -> None:
    seen = set()
    for node in _walk_pages(category.root_pages):
        path = node.full_path()
        if path in seen:
            raise ValueError(f"Duplicate page path: {path}")
        seen.add(path)


def _is_valid_image_resource(resource: str) -> bool:
    value = (resource or "").strip()
    if not value:
        return False
    lower = value.lower()
    return lower.startswith("/texture/") and lower.endswith(".dds")


def validate_images(category: HolocronCategory) -> None:
    for node in _walk_pages(category.root_pages):
        for image in node.images:
            if not _is_valid_image_resource(image.resource):
                raise ValueError(
                    f"Invalid image resource '{image.resource}' on {node.full_path()}. "
                    "Images must be /texture/<name>.dds"
                )


def _category_uses_loc(category: HolocronCategory, nodes: List[PageNode] | None = None) -> bool:
    pages = nodes or _walk_pages(category.root_pages)
    for node in pages:
        if (node.title_token or "").startswith("@loc_") or (node.content_token or "").startswith("@loc_"):
            return True
    return category.name.lower() == "planets"


def build_kb_rows(
    category: HolocronCategory,
    nodes: List[PageNode] | None = None,
    use_loc: bool | None = None,
) -> List[List[str]]:
    rows: List[List[str]] = []
    if use_loc is None:
        use_loc = _category_uses_loc(category, nodes)

    def add_node(node: PageNode) -> None:
        parent_path = ""
        if node.parent is not None:
            parent_path = node.parent.full_path()

        token_key = node.short_name.lower()
        title_token = node.title_token
        if not title_token:
            if use_loc and node.parent is not None:
                title_token = f"@loc_n:{token_key}"
            else:
                title_token = f"@kb/kb_{category.name}_n:{token_key}"
        rows.append([
            parent_path,
            node.short_name,
            "Page",
            title_token,
            "",
        ])

        if node.images:
            for i, image in enumerate(node.images, start=1):
                name = image.name or f"Image{i}"
                rows.append([
                    node.full_path(),
                    name,
                    "Image",
                    image.resource,
                    "",
                ])

        if node.content:
            content_token = node.content_token
            if not content_token:
                if use_loc and node.parent is not None:
                    content_token = f"@loc_d:{token_key}"
                else:
                    content_token = f"@kb/kb_{category.name}_d:{token_key}"
            rows.append([
                node.full_path(),
                "Text",
                "String",
                content_token,
                "",
            ])

        for link in node.links:
            key = link.key or sanitize_key(link.label)
            name = link.name or f"Link{key.capitalize()}"
            label_token = link.label_token or f"@kb/kb_{category.name}_d:{key}"
            rows.append([
                node.full_path(),
                name,
                "LinkButton",
                label_token,
                link.target,
            ])

        for child in node.children:
            add_node(child)

    for root in category.root_pages:
        add_node(root)

    return rows


def _split_token(token: str) -> Tuple[str, str]:
    t = (token or "").strip()
    if not t.startswith("@") or ":" not in t:
        return "", ""
    table, key = t[1:].split(":", 1)
    return table.strip(), key.strip()


def _add_unique(items: List[Tuple[str, str]], seen: set, key: str, value: str) -> None:
    if not key:
        return
    if key in seen:
        return
    items.append((key, value))
    seen.add(key)


def build_stf_entries(
    category: HolocronCategory,
    nodes: List[PageNode] | None = None,
    use_loc: bool | None = None,
) -> Tuple[List[StfEntry], List[StfEntry], Dict[str, List[StfEntry]]]:
    names: List[Tuple[str, str]] = []
    descs: List[Tuple[str, str]] = []
    extra_tables: Dict[str, List[Tuple[str, str]]] = {}
    extra_seen: Dict[str, set] = {}
    if use_loc is None:
        use_loc = _category_uses_loc(category, nodes)

    pages = nodes or _walk_pages(category.root_pages)
    for node in pages:
        token_key = node.short_name.lower()
        name_token = node.title_token
        if not name_token:
            if use_loc and node.parent is not None:
                name_token = f"@loc_n:{token_key}"
            else:
                name_token = f"@kb/kb_{category.name}_n:{token_key}"
        desc_token = node.content_token
        if not desc_token:
            if use_loc and node.parent is not None:
                desc_token = f"@loc_d:{token_key}"
            else:
                desc_token = f"@kb/kb_{category.name}_d:{token_key}"

        if name_token.startswith(f"@kb/kb_{category.name}_n:"):
            names.append((token_key, node.title))
        else:
            table, key = _split_token(name_token)
            if table and key:
                extra_tables.setdefault(table, [])
                extra_seen.setdefault(table, set())
                _add_unique(extra_tables[table], extra_seen[table], key, node.title)

        if desc_token.startswith(f"@kb/kb_{category.name}_d:"):
            descs.append((token_key, node.content))
        else:
            table, key = _split_token(desc_token)
            if table and key:
                extra_tables.setdefault(table, [])
                extra_seen.setdefault(table, set())
                _add_unique(extra_tables[table], extra_seen[table], key, node.content)

        for link in node.links:
            key = link.key or sanitize_key(link.label)
            label_token = link.label_token or f"@kb/kb_{category.name}_d:{key}"
            if label_token.startswith(f"@kb/kb_{category.name}_d:"):
                descs.append((key, link.label))
            else:
                table, tkey = _split_token(label_token)
                if table and tkey:
                    extra_tables.setdefault(table, [])
                    extra_seen.setdefault(table, set())
                    _add_unique(extra_tables[table], extra_seen[table], tkey, link.label)

    extra_entries = {k: build_entries_from_dict(v) for k, v in extra_tables.items()}
    return build_entries_from_dict(names), build_entries_from_dict(descs), extra_entries


def _extract_token_order(rows: List[List[str]], suffix: str) -> List[str]:
    tokens: List[str] = []
    seen = set()
    for r in rows:
        if len(r) < 4:
            continue
        data1 = r[3]
        if not isinstance(data1, str):
            continue
        if data1.startswith("@kb/") and ":" in data1:
            part, token = data1.split(":", 1)
            if part.endswith(f"_{suffix}"):
                key = token.strip()
                if key and key not in seen:
                    tokens.append(key)
                    seen.add(key)
    return tokens


def _apply_id_order(entries: List[StfEntry], order: List[str]) -> List[StfEntry]:
    by_key = {e.key: e for e in entries}
    assigned: List[StfEntry] = []
    current_id = 1

    for key in order:
        e = by_key.get(key)
        if e is None:
            continue
        e.string_id = current_id
        assigned.append(e)
        current_id += 1

    for key, e in by_key.items():
        if e in assigned:
            continue
        e.string_id = current_id
        assigned.append(e)
        current_id += 1

    return assigned


def generate_files(category: HolocronCategory, output_root: str, language: str = "en") -> Dict[str, str]:
    validate_unique_paths(category)
    validate_images(category)

    pages = _walk_pages(category.root_pages)
    use_loc = _category_uses_loc(category, pages)

    rows = build_kb_rows(category, nodes=pages, use_loc=use_loc)
    table = build_kb_table(rows, type_id=COLTYPE_STRING_V1)

    kb_table_path = os.path.join(output_root, "datatables", "knowledgebase", f"{category.name}.iff")
    kb_name_path = os.path.join(output_root, "string", language, "kb", f"kb_{category.name}_n.stf")
    kb_desc_path = os.path.join(output_root, "string", language, "kb", f"kb_{category.name}_d.stf")

    os.makedirs(os.path.dirname(kb_table_path), exist_ok=True)
    os.makedirs(os.path.dirname(kb_name_path), exist_ok=True)

    write_dt_iff(kb_table_path, table, version="0001")

    names, descs, extra_entries = build_stf_entries(category, nodes=pages, use_loc=use_loc)

    n_order = _extract_token_order(rows, "n")
    d_order = _extract_token_order(rows, "d")
    names = _apply_id_order(names, n_order)
    descs = _apply_id_order(descs, d_order)

    write_stf(kb_name_path, names)
    write_stf(kb_desc_path, descs)

    extra_paths: Dict[str, str] = {}
    for table_name, entries in extra_entries.items():
        if not entries:
            continue
        out_path = os.path.join(output_root, "string", language, f"{table_name}.stf")
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        write_stf(out_path, entries)
        extra_paths[table_name] = out_path

    return {
        "datatable": kb_table_path,
        "names": kb_name_path,
        "descriptions": kb_desc_path,
        "extra": extra_paths,
    }


def generate_project(project: HolocronProject, output_root: str, language: str = "en") -> Dict[str, Dict[str, str]]:
    results: Dict[str, Dict[str, str]] = {}
    seen = set()
    for cat in project.categories:
        if cat.name in seen:
            raise ValueError(f"Duplicate category name: {cat.name}")
        seen.add(cat.name)
        results[cat.name] = generate_files(cat, output_root, language=language)

    filelist_path = os.path.join(output_root, "datatables", "knowledgebase", "filelist.iff")
    write_filelist_from_categories(filelist_path, [c.name for c in project.categories])

    return results
