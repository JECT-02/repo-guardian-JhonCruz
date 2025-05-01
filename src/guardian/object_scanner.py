import hashlib
import zlib
from dataclasses import dataclass
from pathlib import Path


@dataclass
class GitObject:
    """Representa un objeto Git con su tipo, datos y hash."""
    type: str  # "blob", "commit", "tree", "tag"
    data: bytes
    sha: str   # Hash SHA-1 calculado

def read_loose(path: Path) -> GitObject:
    """
    Lee y valida un objeto Git suelto (loose).
    Args:
        path: Ruta al archivo en .git/objects (ej: "ab/1234...")
    Returns:
        GitObject validado
    Raises:
        ValueError: Si el objeto está corrupto o es inválido
    """
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
        raise ValueError(f"Size mismatch: expected {size_str}, got {len(body)}")

    return GitObject(type=obj_type, data=body, sha=sha)
