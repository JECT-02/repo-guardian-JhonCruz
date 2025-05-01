import hashlib
import zlib
from pathlib import Path

import pytest

from guardian.object_scanner import read_loose


@pytest.fixture
def valid_blob_path(tmp_path):
    """Fixture que crea un blob Git válido para pruebas."""
    content = b"test content"
    header = f"blob {len(content)}\0".encode()
    full_content = header + content
    sha = hashlib.sha1(full_content).hexdigest()

    obj_dir = tmp_path / "objects" / sha[:2]
    obj_dir.mkdir(parents=True)
    obj_path = obj_dir / sha[2:]
    obj_path.write_bytes(zlib.compress(full_content))

    return obj_path


def test_read_loose_valid(valid_blob_path):
    """Prueba lectura de objeto válido."""
    obj = read_loose(valid_blob_path)
    assert obj.type == "blob"
    assert obj.sha == valid_blob_path.parent.name + valid_blob_path.name


def test_read_loose_nonexistent_path():
    """Prueba manejo de path inexistente."""
    with pytest.raises(ValueError, match="does not exist"):
        read_loose(Path("/nonexistent/path"))


def test_read_loose_corrupt_zlib(tmp_path):
    """Prueba detección de datos zlib corruptos."""
    corrupt_path = tmp_path / "corrupt"
    corrupt_path.write_bytes(b"invalid zlib data")
    with pytest.raises(ValueError, match="Corrupt zlib data"):
        read_loose(corrupt_path)


def test_read_loose_invalid_header(tmp_path):
    """Prueba detección de header inválido."""
    invalid_data = zlib.compress(b"invalidheader")
    path = tmp_path / "invalid"
    path.write_bytes(invalid_data)
    with pytest.raises(ValueError, match="Invalid object format"):
        read_loose(path)


def test_read_loose_size_mismatch(valid_blob_path):
    """Prueba detección de discrepancia en tamaño."""
    with open(valid_blob_path, "rb") as f:
        decompressed = zlib.decompress(f.read())
    
    header, _, body = decompressed.partition(b"\x00")
    
    # Modificar solo el tamaño declarado manteniendo el mismo contenido real
    corrupted_header = header.replace(
        f"blob {len(body)}".encode(), 
        f"blob {len(body)+1}".encode()
    )
    corrupted_data = corrupted_header + b"\x00" + body
    
    # Calcular el nuevo SHA-1
    new_sha = hashlib.sha1(corrupted_data).hexdigest()
    
    # Crear el directorio basado en los primeros dos caracteres del nuevo SHA-1
    obj_dir = valid_blob_path.parent.parent / new_sha[:2]
    obj_dir.mkdir(parents=True, exist_ok=True)
    corrupted_path = obj_dir / new_sha[2:]
    corrupted_path.write_bytes(zlib.compress(corrupted_data))
    
    with pytest.raises(ValueError, match="Size mismatch"):
        read_loose(corrupted_path)


def test_read_loose_sha_mismatch(valid_blob_path):
    """Prueba detección de discrepancia en SHA-1."""
    with open(valid_blob_path, "rb") as f:
        decompressed = zlib.decompress(f.read())

    corrupted_data = decompressed.replace(b"test", b"corr")
    corrupted_path = valid_blob_path.parent / "corrupted_sha"
    corrupted_path.write_bytes(zlib.compress(corrupted_data))

    with pytest.raises(ValueError, match="SHA-1 mismatch"):
        read_loose(corrupted_path)