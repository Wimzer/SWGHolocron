from __future__ import annotations

from dataclasses import dataclass
from typing import List
import struct

from .dtii_writer import (
    COLTYPE_INT,
    COLTYPE_FLOAT,
    COLTYPE_STRING,
    COLTYPE_HASHSTRING,
    COLTYPE_ENUM,
    COLTYPE_BOOL,
    COLTYPE_BITVECTOR,
    COLTYPE_COMMENT,
)


@dataclass
class DataTableColumn:
    name: str
    type_id: int


@dataclass
class DataTable:
    columns: List[DataTableColumn]
    rows: List[List]


def _ensure_len(buf: bytes, offset: int, size: int, label: str = "buffer") -> None:
    if offset + size > len(buf):
        raise ValueError(
            f"Truncated {label}: need {size} bytes at offset {offset}, have {len(buf) - offset}"
        )


def _read_tag(buf: bytes, offset: int) -> str:
    _ensure_len(buf, offset, 4, "tag")
    return buf[offset:offset + 4].decode("ascii")


def _read_u32be(buf: bytes, offset: int) -> int:
    _ensure_len(buf, offset, 4, "u32be")
    return struct.unpack_from(">I", buf, offset)[0]


def _read_i32le(buf: bytes, offset: int) -> int:
    _ensure_len(buf, offset, 4, "i32le")
    return struct.unpack_from("<i", buf, offset)[0]


def _read_f32le(buf: bytes, offset: int) -> float:
    _ensure_len(buf, offset, 4, "f32le")
    return struct.unpack_from("<f", buf, offset)[0]


def _read_cstring(buf: bytes, offset: int) -> tuple[str, int]:
    if offset >= len(buf):
        raise ValueError("Truncated cstring: no data")
    end = offset
    while end < len(buf) and buf[end] != 0:
        end += 1
    s = buf[offset:end].decode("utf-8")
    return s, end + 1


def parse_dt_iff(data: bytes) -> DataTable:
    off = 0
    if _read_tag(data, off) != "FORM":
        raise ValueError("Not an IFF FORM")
    off += 4
    _len = _read_u32be(data, off)
    off += 4
    if _read_tag(data, off) != "DTII":
        raise ValueError("Not a DTII file")
    off += 4

    if _read_tag(data, off) != "FORM":
        raise ValueError("Missing inner FORM")
    off += 4
    inner_len = _read_u32be(data, off)
    off += 4
    version = _read_tag(data, off)
    if version not in ("0000", "0001"):
        raise ValueError(f"Unsupported DTII version: {version}")
    off += 4

    inner_end = off + (inner_len - 4)
    if inner_end > len(data):
        raise ValueError("Inner FORM length exceeds file size")

    columns: List[DataTableColumn] = []
    rows: List[List] = []

    while off < inner_end:
        tag = _read_tag(data, off)
        off += 4
        clen = _read_u32be(data, off)
        off += 4
        _ensure_len(data, off, clen, f"chunk {tag}")
        chunk = data[off:off + clen]
        off += clen

        if tag == "COLS":
            coff = 0
            num_cols = _read_i32le(chunk, coff)
            coff += 4
            for _ in range(num_cols):
                name, coff = _read_cstring(chunk, coff)
                columns.append(DataTableColumn(name=name, type_id=COLTYPE_STRING))
        elif tag == "TYPE":
            coff = 0
            use_short = (len(chunk) == len(columns) * 2)
            for i in range(len(columns)):
                if use_short:
                    _ensure_len(chunk, coff, 2, "type_id")
                    type_id = struct.unpack_from("<h", chunk, coff)[0]
                    coff += 2
                else:
                    type_id = _read_i32le(chunk, coff)
                    coff += 4
                columns[i].type_id = type_id
        elif tag == "ROWS":
            coff = 0
            num_rows = _read_i32le(chunk, coff)
            coff += 4
            for _ in range(num_rows):
                row = []
                for col in columns:
                    t = col.type_id
                    if t in (COLTYPE_INT, COLTYPE_ENUM, COLTYPE_BITVECTOR, COLTYPE_HASHSTRING):
                        row.append(_read_i32le(chunk, coff))
                        coff += 4
                    elif t == COLTYPE_FLOAT:
                        row.append(_read_f32le(chunk, coff))
                        coff += 4
                    elif t in (COLTYPE_STRING, COLTYPE_COMMENT):
                        s, coff = _read_cstring(chunk, coff)
                        row.append(s)
                    elif t == COLTYPE_BOOL:
                        row.append(_read_i32le(chunk, coff) != 0)
                        coff += 4
                    else:
                        s, coff = _read_cstring(chunk, coff)
                        row.append(s)
                rows.append(row)
        else:
            continue

    return DataTable(columns=columns, rows=rows)
