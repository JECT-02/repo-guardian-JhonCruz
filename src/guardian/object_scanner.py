import zlib
from pathlib import Path
from dataclasses import dataclass
import hashlib

@dataclass
class GitObject:
    type: str  # "blob", "commit", "tree", "tag"
    data: bytes
    sha: str   # Hash SHA-1 calculado

def read_loose(path: Path) -> GitObject:
    """
    Lee un objeto Git suelto (loose) y valida su integridad.
    
    Args:
        path: Ruta al archivo en .git/objects (ej: "ab/1234...").
    
    Returns:
        GitObject con tipo, datos y hash.
    
    Raises:
        ValueError: Si el objeto está corrupto o es inválido.
    """
    if not path.exists():
        raise ValueError(f"Path {path} does not exist")

    with open(path, "rb") as f:
        raw_data = f.read()

    try:
        decompressed = zlib.decompress(raw_data)
    except zlib.error as e:
        raise ValueError(f"Corrupt zlib data: {e}")

    header, _, body = decompressed.partition(b"\x00")
    if not header or not body:
        raise ValueError("Invalid object format: missing header or body")

    try:
        obj_type, size_str = header.decode().split()
    except UnicodeDecodeError:
        raise ValueError("Invalid header encoding")

    # Validar tamaño primero (para casos de prueba de tamaño)
    if int(size_str) != len(body):
        raise ValueError(f"Size mismatch: expected {size_str}, got {len(body)}")

    # Luego validar el SHA-1
    full_content = header + b"\x00" + body
    sha = hashlib.sha1(full_content).hexdigest()
    expected_sha = path.parent.name + path.name
    if sha != expected_sha:
        raise ValueError(f"SHA-1 mismatch: expected {expected_sha}, got {sha}")

    return GitObject(type=obj_type, data=body, sha=sha)