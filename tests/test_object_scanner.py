import binascii
import struct
import zlib

import pytest
from guardian.object_scanner import read_packfile


@pytest.fixture
def valid_packfile(tmp_path):
    """Crea un packfile válido de prueba."""
    pack_dir = tmp_path / "objects" / "pack"
    pack_dir.mkdir(parents=True)

    # Crear objeto blob válido
    content = b"test content"
    header = f"blob {len(content)}\0".encode()
    full_content = header + content
    compressed = zlib.compress(full_content)
    crc = binascii.crc32(compressed)

    # Cabecera del packfile (12 bytes)
    pack_header = struct.pack(">4sII", b"PACK", 2, 1)

    # Header de objeto (type=3 para blob)
    size = len(compressed)
    obj_header = bytearray()
    byte = 0b10000000 | (3 << 4) | (size & 0b1111)
    obj_header.append(byte)
    size >>= 4
    while size > 0:
        byte = 0b10000000 | (size & 0b1111111)
        obj_header.append(byte)
        size >>= 7

    # Datos completos del objeto
    obj_entry = bytes(obj_header) + compressed + struct.pack(">I", crc)

    # Packfile completo
    pack_data = pack_header + obj_entry
    pack_path = pack_dir / "valid.pack"
    pack_path.write_bytes(pack_data)

    return pack_path


def test_read_packfile_invalid_signature(tmp_path):
    """Prueba detección de firma inválida."""
    invalid_pack = tmp_path / "invalid.pack"
    invalid_pack.write_bytes(b"INVALID" + b"\x00"*8)
    with pytest.raises(ValueError, match="Invalid packfile signature"):
        read_packfile(invalid_pack)


def test_read_packfile_corrupt_crc(tmp_path):
    """Prueba detección de CRC corrupto."""
    pack_dir = tmp_path / "objects" / "pack"
    pack_dir.mkdir(parents=True)

    content = b"test"
    header = f"blob {len(content)}\0".encode()
    full_content = header + content
    compressed = zlib.compress(full_content)
    crc = binascii.crc32(compressed) ^ 0xFFFFFFFF  # CRC corrupto

    pack_header = struct.pack(">4sII", b"PACK", 2, 1)

    # Header de objeto con tamaño correcto
    size = len(compressed)
    obj_header = bytearray()
    byte = 0b10000000 | (3 << 4) | (size & 0b1111)
    obj_header.append(byte)
    size >>= 4
    while size > 0:
        byte = 0b10000000 | (size & 0b1111111)
        obj_header.append(byte)
        size >>= 7

    obj_entry = bytes(obj_header) + compressed + struct.pack(">I", crc)

    corrupt_pack = pack_dir / "corrupt.pack"
    corrupt_pack.write_bytes(pack_header + obj_entry)

    with pytest.raises(ValueError, match="Invalid CRC at offset"):
        read_packfile(corrupt_pack)


def test_read_packfile_truncated(tmp_path):
    """Prueba detección de packfile truncado."""
    pack_dir = tmp_path / "objects" / "pack"
    pack_dir.mkdir(parents=True)

    truncated = struct.pack(">4sII", b"PACK", 2, 1)[:8]
    pack_path = pack_dir / "truncated.pack"
    pack_path.write_bytes(truncated)

    with pytest.raises(ValueError, match="Packfile too small"):
        read_packfile(pack_path)
