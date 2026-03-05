from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List
import struct


@dataclass
class StfEntry:
    string_id: int
    crc: int
    text: str


@dataclass
class StfFile:
    version: int
    next_free_id: int
    entries: List[StfEntry]
    key_map: Dict[str, int]

    def map_by_crc(self) -> Dict[int, str]:
        return {e.crc: e.text for e in self.entries}

    def map_by_id(self) -> Dict[int, str]:
        return {e.string_id: e.text for e in self.entries}

    def map_by_key(self) -> Dict[str, str]:
        by_id = self.map_by_id()
        return {k: by_id.get(v, "") for k, v in self.key_map.items()}


def read_stf(path: str) -> StfFile:
    with open(path, "rb") as f:
        data = f.read()

    offset = 0
    magic = struct.unpack_from("<I", data, offset)[0]
    offset += 4
    if magic != 0x0000ABCD:
        raise ValueError("Invalid STF magic")

    version = struct.unpack_from("<B", data, offset)[0]
    offset += 1
    if version not in (0, 1):
        raise ValueError(f"Unsupported STF version: {version}")

    next_free_id = struct.unpack_from("<I", data, offset)[0]
    offset += 4
    num_entries = struct.unpack_from("<I", data, offset)[0]
    offset += 4

    entries: List[StfEntry] = []
    for _ in range(num_entries):
        if offset + 12 > len(data):
            break
        string_id = struct.unpack_from("<I", data, offset)[0]
        offset += 4
        crc = struct.unpack_from("<I", data, offset)[0]
        offset += 4
        str_len = struct.unpack_from("<I", data, offset)[0]
        offset += 4
        if offset + str_len * 2 > len(data):
            break
        text = data[offset:offset + str_len * 2].decode("utf-16le")
        offset += str_len * 2
        entries.append(StfEntry(string_id=string_id, crc=crc, text=text))

    key_map: Dict[str, int] = {}
    for _ in range(num_entries):
        if offset + 8 > len(data):
            break
        sid = struct.unpack_from("<I", data, offset)[0]
        offset += 4
        buflen = struct.unpack_from("<I", data, offset)[0]
        offset += 4
        if offset + buflen > len(data):
            break
        name = data[offset:offset + buflen].decode("ascii", errors="ignore")
        offset += buflen
        if name:
            key_map[name] = sid

    return StfFile(version=version, next_free_id=next_free_id, entries=entries, key_map=key_map)
