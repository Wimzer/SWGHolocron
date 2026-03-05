from __future__ import annotations

import os
from typing import Iterable, List

from .dtii_writer import DataTable, DataTableColumn, write_dt_iff, COLTYPE_STRING_V1


def _normalize_name(name: str) -> str:
    if not name:
        return name
    if name.lower().endswith(".iff"):
        return name
    return f"{name}.iff"


def write_filelist_from_categories(path: str, categories: Iterable[str]) -> None:
    rows: List[List[str]] = [[_normalize_name(c)] for c in categories]
    table = DataTable(columns=[DataTableColumn("FileName", COLTYPE_STRING_V1)], rows=rows)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    write_dt_iff(path, table, version="0001")
