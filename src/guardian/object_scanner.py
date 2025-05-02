import binascii
import hashlib
import struct
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

PACK_SIGNATURE = b'PACK'
PACK_VERSION = 2


@dataclass
class GitObject:
    type: str
    data: bytes
    sha: str


def read_loose(path: Path) -> GitObject:
    """Lee un objeto Git suelto (loose object)."""
    if not path.exists():
        raise ValueError(f"Path {path} does not exist")

    with open(path, "rb") as f:
        raw_data = f.read()

    try:
        decompressed = zlib.decompress(raw_data)
    except zlib.error as e:
        raise ValueError(f"Corrupt zlib data: {e}") from e

    header, _, body = decompressed.partition(b"\x00")
    if not header or not body:
        raise ValueError("Invalid object format: missing header or body")

    try:
        obj_type, size_str = header.decode().split()
    except (UnicodeDecodeError, ValueError) as e:
        raise ValueError("Invalid header encoding") from e

    full_content = header + b"\x00" + body
    computed_sha = hashlib.sha1(full_content).hexdigest()

    expected_dir = computed_sha[:2]
    expected_filename = computed_sha[2:]

    if path.parent.name != expected_dir or path.name != expected_filename:
        raise ValueError(
            f"SHA-1 mismatch: expected {computed_sha}, "
            f"got {path.parent.name}{path.name}"
        )

    if int(size_str) != len(body):
        raise ValueError(f"Size mismatch: expected {size_str}, got {len(body)}")

    return GitObject(type=obj_type, data=body, sha=computed_sha)


def read_packfile(pack_path: Path) -> List[GitObject]:
    """Lee y valida un archivo packfile de Git."""
    if not pack_path.exists():
        raise ValueError(f"Packfile {pack_path} does not exist")

    with open(pack_path, 'rb') as f:
        data = f.read()

    if len(data) < 12:
        raise ValueError("Packfile too small to be valid")

    signature = data[:4]
    version = struct.unpack('>I', data[4:8])[0]
    num_objects = struct.unpack('>I', data[8:12])[0]

    if signature != PACK_SIGNATURE:
        raise ValueError("Invalid packfile signature")
    if version != PACK_VERSION:
        raise ValueError(f"Unsupported packfile version: {version}")

    objects = []
    offset = 12

    for _ in range(num_objects):
        try:
            obj, offset = _read_pack_entry(data, offset)
            objects.append(obj)
        except (ValueError, struct.error, zlib.error) as e:
            if "CRC" in str(e):
                raise ValueError(f"Invalid CRC at offset {offset-4}") from e
            raise ValueError(f"Error reading packfile: {str(e)}") from e

    return objects


def _read_pack_entry(data: bytes, offset: int) -> Tuple[GitObject, int]:
    """Lee una entrada individual en un packfile."""
    if offset >= len(data):
        raise ValueError("Unexpected end of packfile")

    byte = data[offset]
    offset += 1

    obj_type = (byte >> 4) & 0b0111
    size = byte & 0b1111
    shift = 4

    while byte & 0x80:
        if offset >= len(data):
            raise ValueError("Truncated object header")
        byte = data[offset]
        offset += 1
        size |= (byte & 0x7f) << shift
        shift += 7

    type_map: Dict[int, str] = {1: "commit", 2: "tree", 3: "blob", 4: "tag"}
    obj_type_str = type_map.get(obj_type, "unknown")

    if offset + size + 4 > len(data):
        raise ValueError(
            f"Truncated object data (missing data or CRC) - "
            f"needed {offset+size+4}, have {len(data)}"
        )

    compressed_data = data[offset:offset+size]
    crc_offset = offset + size

    stored_crc = struct.unpack('>I', data[crc_offset:crc_offset+4])[0]
    computed_crc = binascii.crc32(compressed_data) & 0xffffffff

    if stored_crc != computed_crc:
        raise ValueError(
            f"CRC mismatch at offset {crc_offset}: "
            f"stored {stored_crc:08x} != computed {computed_crc:08x}"
        )

    try:
        raw_data = zlib.decompress(compressed_data)
    except zlib.error as e:
        raise ValueError(f"Invalid zlib data: {str(e)}") from e

    header = f"{obj_type_str} {len(raw_data)}\0".encode()
    obj = GitObject(
        type=obj_type_str,
        data=raw_data,
        sha=hashlib.sha1(header + raw_data).hexdigest()
    )

    return obj, crc_offset + 4
