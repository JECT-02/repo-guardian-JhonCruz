import binascii
import hashlib
import struct
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

PACK_SIGNATURE = b'PACK'
PACK_VERSION = 2


@dataclass
class GitObject:
    type: str
    data: bytes
    sha: str


def read_loose(path: Path) -> GitObject:
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
    except UnicodeDecodeError as e:
        raise ValueError("Invalid header encoding") from e

    full_content = header + b"\x00" + body
    sha = hashlib.sha1(full_content).hexdigest()
    expected_sha = path.parent.name + path.name

    if sha != expected_sha:
        raise ValueError(f"SHA-1 mismatch: expected {expected_sha}, got {sha}")

    if int(size_str) != len(body):
        msg = f"Size mismatch: expected {size_str}, got {len(body)}"
        raise ValueError(msg)

    return GitObject(type=obj_type, data=body, sha=sha)


def read_packfile(pack_path: Path) -> List[GitObject]:
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
        msg = f"Unsupported packfile version: {version}"
        raise ValueError(msg)

    objects = []
    offset = 12

    for _ in range(num_objects):
        try:
            obj, offset = _read_pack_entry(data, offset)
            objects.append(obj)
        except (ValueError, struct.error, zlib.error) as e:
            if "CRC" in str(e):
                raise ValueError(f"Invalid CRC at offset {offset-4}") from e
            msg = f"Error reading packfile: {str(e)}"
            raise ValueError(msg) from e

    return objects


def _read_pack_entry(data: bytes, offset: int) -> Tuple[GitObject, int]:
    """Lee una entrada individual en un packfile."""
    if offset >= len(data):
        raise ValueError("Unexpected end of packfile")

    # Leer cabecera de tamaño variable
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

    type_map = {1: "commit", 2: "tree", 3: "blob", 4: "tag"}
    obj_type_str = type_map.get(obj_type, "unknown")

    # Verificar que hay suficientes datos para el objeto + CRC
    if offset + size + 4 > len(data):
        raise ValueError("Truncated object data (missing data or CRC)")

    # Extraer datos comprimidos
    compressed_data = data[offset:offset+size]
    crc_offset = offset + size

    # Leer y verificar CRC
    stored_crc = struct.unpack('>I', data[crc_offset:crc_offset+4])[0]
    computed_crc = binascii.crc32(compressed_data) & 0xffffffff

    if stored_crc != computed_crc:
        raise ValueError(f"CRC mismatch at offset {crc_offset}")

    # Descomprimir datos
    try:
        raw_data = zlib.decompress(compressed_data)
    except zlib.error as e:
        raise ValueError(f"Invalid zlib data: {str(e)}") from e

    # Crear objeto Git
    header = f"{obj_type_str} {len(raw_data)}\0".encode()
    obj = GitObject(
        type=obj_type_str,
        data=raw_data,
        sha=hashlib.sha1(header + raw_data).hexdigest()
    )

    return obj, crc_offset + 4
