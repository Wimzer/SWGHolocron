from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List
import struct

COLTYPE_INT = 0
COLTYPE_FLOAT = 1
COLTYPE_STRING = 2
COLTYPE_HASHSTRING = 3
COLTYPE_ENUM = 4
COLTYPE_BOOL = 5
COLTYPE_BITVECTOR = 6
COLTYPE_COMMENT = 7
COLTYPE_PACKEDOBJVARS = 8

COLTYPE_STRING_V1 = 115


@dataclass
class DataTableColumn:
    name: str
    type_id: int = COLTYPE_STRING


@dataclass
class DataTable:
    columns: List[DataTableColumn]
    rows: List[List[str]]


def _tag(tag: str) -> bytes:
    if len(tag) != 4:
        raise ValueError(f"Tag must be 4 chars: {tag}")
    return tag.encode("ascii")


def _chunk(tag: str, payload: bytes) -> bytes:
    return _tag(tag) + struct.pack(">I", len(payload)) + payload


def _form(tag: str, content: bytes) -> bytes:
    return _tag("FORM") + struct.pack(">I", len(content) + 4) + _tag(tag) + content


def _write_string(value: str) -> bytes:
    return value.encode("utf-8") + b"\x00"


def build_dt_iff(table: DataTable, version: str = "0000") -> bytes:
    cols_payload = bytearray()
    cols_payload += struct.pack("<i", len(table.columns))
    for col in table.columns:
        cols_payload += _write_string(col.name)
    cols_chunk = _chunk("COLS", bytes(cols_payload))

    type_payload = bytearray()
    use_short = (version == "0001")
    for col in table.columns:
        if use_short:
            type_payload += struct.pack("<h", int(col.type_id))
        else:
            type_payload += struct.pack("<i", int(col.type_id))
    type_chunk = _chunk("TYPE", bytes(type_payload))

    rows_payload = bytearray()
    rows_payload += struct.pack("<i", len(table.rows))
    for row in table.rows:
        if len(row) != len(table.columns):
            raise ValueError("Row length does not match column count")
        for value in row:
            rows_payload += _write_string(str(value))
    rows_chunk = _chunk("ROWS", bytes(rows_payload))

    inner = cols_chunk + type_chunk + rows_chunk
    dt_form = _form(version, inner)
    return _form("DTII", dt_form)


def write_dt_iff(path: str, table: DataTable, version: str = "0000") -> None:
    data = build_dt_iff(table, version=version)
    with open(path, "wb") as f:
        f.write(data)


def build_kb_table(rows: Iterable[List[str]], type_id: int = COLTYPE_STRING) -> DataTable:
    cols = [
        DataTableColumn("Parent", type_id),
        DataTableColumn("Name", type_id),
        DataTableColumn("Type", type_id),
        DataTableColumn("Data1", type_id),
        DataTableColumn("Data2", type_id),
    ]
    return DataTable(columns=cols, rows=list(rows))
