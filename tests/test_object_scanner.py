import binascii
import hashlib
import struct
import zlib

import pytest
from guardian.object_scanner import read_loose, read_packfile


@pytest.fixture
def valid_packfile(tmp_path):
    """Crea un packfile válido de prueba"""
    pack_dir = tmp_path / "objects" / "pack"
    pack_dir.mkdir(parents=True)

    content = b"test"
    header = f"blob {len(content)}\0".encode()
    full_content = header + content

    compressed = zlib.compress(full_content)
    crc = binascii.crc32(compressed)

    pack_header = struct.pack(">4sII", b"PACK", 2, 1)

    size = len(compressed)
    obj_header = bytearray()

    byte = 0b10000000 | (3 << 4) | (size & 0b1111)
    obj_header.append(byte)
    size >>= 4

    byte = size & 0b01111111
    obj_header.append(byte)

    pack_content = (
        pack_header +
        bytes(obj_header) +
        compressed +
        struct.pack(">I", crc)
    )

    pack_path = pack_dir / "valid.pack"
    pack_path.write_bytes(pack_content)

    return pack_path


def test_read_loose_valid_object(tmp_path):
    """Prueba lectura correcta de objeto loose"""
    content = b"test"
    header = f"blob {len(content)}\0".encode()
    full_content = header + content

    computed_sha = hashlib.sha1(full_content).hexdigest()
    obj_dir = tmp_path / computed_sha[:2]
    obj_dir.mkdir()
    obj_file = obj_dir / computed_sha[2:]

    compressed = zlib.compress(full_content)
    obj_file.write_bytes(compressed)

    result = read_loose(obj_file)
    assert result.type == "blob"
    assert result.data == content
    assert result.sha == computed_sha


def test_read_loose_invalid_object(tmp_path):
    """Prueba lectura de objeto inválido"""
    obj_file = tmp_path / "invalid"
    obj_file.write_bytes(zlib.compress(b"invalid data"))

    with pytest.raises(ValueError):
        read_loose(obj_file)


def test_read_packfile_invalid_signature(tmp_path):
    """Prueba detección de firma inválida"""
    invalid_pack = tmp_path / "invalid.pack"
    invalid_pack.write_bytes(b"INVALID" + b"\x00"*8)

    with pytest.raises(ValueError, match="Invalid packfile signature"):
        read_packfile(invalid_pack)


def test_read_packfile_corrupt_crc(tmp_path):
    """Prueba detección de CRC corrupto"""
    pack_dir = tmp_path / "objects" / "pack"
    pack_dir.mkdir(parents=True)

    content = b"test"
    header = f"blob {len(content)}\0".encode()
    full_content = header + content
    compressed = zlib.compress(full_content)
    crc = binascii.crc32(compressed) ^ 0xFFFFFFFF

    pack_header = struct.pack(">4sII", b"PACK", 2, 1)
    size = len(compressed)

    obj_header = bytearray()
    byte = 0b10000000 | (3 << 4) | (size & 0b1111)
    obj_header.append(byte)
    size >>= 4
    byte = size & 0b01111111
    obj_header.append(byte)

    obj_entry = bytes(obj_header) + compressed + struct.pack(">I", crc)
    corrupt_pack = pack_dir / "corrupt.pack"
    corrupt_pack.write_bytes(pack_header + obj_entry)

    with pytest.raises(ValueError, match="Invalid CRC at offset"):
        read_packfile(corrupt_pack)


def test_read_packfile_truncated(tmp_path):
    """Prueba detección de packfile truncado"""
    pack_dir = tmp_path / "objects" / "pack"
    pack_dir.mkdir(parents=True)

    truncated = struct.pack(">4sII", b"PACK", 2, 1)[:8]
    pack_path = pack_dir / "truncated.pack"
    pack_path.write_bytes(truncated)

    with pytest.raises(ValueError, match="Packfile too small"):
        read_packfile(pack_path)


def test_read_packfile_invalid_version(tmp_path):
    """Prueba versión de packfile no soportada"""
    invalid_pack = tmp_path / "invalid_version.pack"
    invalid_pack.write_bytes(b"PACK" + struct.pack(">I", 999) + b"\x00"*8)

    with pytest.raises(ValueError, match="Unsupported packfile version"):
        read_packfile(invalid_pack)


def test_read_packfile_valid(valid_packfile):
    """Prueba lectura exitosa de packfile válido"""
    objects = read_packfile(valid_packfile)
    assert len(objects) == 1
    assert objects[0].type == "blob"
    assert objects[0].data == b"blob 4\x00test"
