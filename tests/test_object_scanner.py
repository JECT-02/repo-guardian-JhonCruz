import hashlib
import zlib
from pathlib import Path
import pytest
from guardian.object_scanner import read_loose, GitObject

@pytest.fixture
def valid_blob_path(tmp_path):
    # Crear un blob válido de prueba
    content = b"test content"  # 12 bytes
    header = f"blob {len(content)}\0".encode()
    full_content = header + content
    sha = hashlib.sha1(full_content).hexdigest()
    
    # Simular estructura .git/objects/ab/1234...
    obj_dir = tmp_path / "objects" / sha[:2]
    obj_dir.mkdir(parents=True)
    obj_path = obj_dir / sha[2:]
    
    compressed = zlib.compress(full_content)
    obj_path.write_bytes(compressed)
    
    return obj_path

def test_read_loose_valid(valid_blob_path):
    obj = read_loose(valid_blob_path)
    assert obj.type == "blob"
    assert obj.sha == valid_blob_path.parent.name + valid_blob_path.name

def test_read_loose_nonexistent_path():
    with pytest.raises(ValueError, match="does not exist"):
        read_loose(Path("/nonexistent/path"))

def test_read_loose_corrupt_zlib(tmp_path):
    corrupt_path = tmp_path / "corrupt"
    corrupt_path.write_bytes(b"invalid zlib data")
    with pytest.raises(ValueError, match="Corrupt zlib data"):
        read_loose(corrupt_path)

def test_read_loose_invalid_header(tmp_path):
    # Header sin \x00
    invalid_data = zlib.compress(b"invalidheader")
    path = tmp_path / "invalid"
    path.write_bytes(invalid_data)
    with pytest.raises(ValueError, match="Invalid object format"):
        read_loose(path)

def test_read_loose_size_mismatch(valid_blob_path):
    with open(valid_blob_path, "rb") as f:
        data = zlib.decompress(f.read())
    
    corrupted_header = header.replace(b"12", b"99")  # Cambiar "12" a "99"
    corrupted_data = corrupted_header + b"\x00" + body
    corrupted_compressed = zlib.compress(corrupted_data)
    
    # Escribir en un nuevo archivo para no afectar el fixture
    new_path = valid_blob_path.parent / "test_size_mismatch"
    new_path.write_bytes(corrupted_compressed)
    
    with pytest.raises(ValueError, match="Size mismatch"):
        read_loose(new_path)

def test_read_loose_sha_mismatch(valid_blob_path):
    # Cambiar el contenido manteniendo exactamente el mismo tamaño (12 bytes)
    with open(valid_blob_path, "rb") as f:
        data = zlib.decompress(f.read())
    
    corrupted_data = data.replace(b"test content", b"corr conteNT")  # 12 bytes
    corrupted_compressed = zlib.compress(corrupted_data)
    
    # Escribir en un NUEVO path con nombre incorrecto
    new_path = valid_blob_path.parent / "ffffffffffffffffffffffffffffffffffff"
    new_path.write_bytes(corrupted_compressed)
    
    with pytest.raises(ValueError, match="SHA-1 mismatch"):
        read_loose(new_path)