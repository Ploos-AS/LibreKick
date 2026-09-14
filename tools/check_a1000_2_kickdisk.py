#!/usr/bin/env python3
"""Static validation for LibreKick A1000.2 WCS payload and disk container."""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import struct
import sys

SECTOR_SIZE = 512
ADF_SIZE = 80 * 2 * 11 * SECTOR_SIZE
WCS_SIZE = 256 * 1024
WCS_BASE = 0x00FC0000
RESET_SP = 0x0007FFFC
ENTRY_PC = WCS_BASE + 8
PAYLOAD_OFFSET = SECTOR_SIZE
MAGIC = b"LIBREKICK-A1000\0"
FORMAT_VERSION = 2
PAYLOAD_MARKER = b"LIBREKICK-A1000.2\0WCS-PAYLOAD\0"
DISK_MARKER = b"LIBREKICK-A1000.2\0KICKDISK-CONTAINER\0"
CODE = bytes.fromhex("33fc00f000dff18060fe")


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "build/a1000")
    payload_path = root / "librekick-a1000.2-wcs.bin"
    disk_path = root / "librekick-a1000.2-kickdisk.adf"
    payload = payload_path.read_bytes()
    disk = disk_path.read_bytes()

    assert len(payload) == WCS_SIZE, f"payload size: expected {WCS_SIZE}, got {len(payload)}"
    assert len(disk) == ADF_SIZE, f"disk size: expected {ADF_SIZE}, got {len(disk)}"
    assert disk[:len(MAGIC)] == MAGIC, "disk magic missing"
    version, offset, length, load_addr, entry_pc, reset_sp = struct.unpack_from(">IIIIII", disk, 16)
    assert version == FORMAT_VERSION, f"format version mismatch: {version}"
    assert offset == PAYLOAD_OFFSET, f"payload offset mismatch: {offset}"
    assert length == WCS_SIZE, f"payload length mismatch: {length}"
    assert load_addr == WCS_BASE, f"WCS base mismatch: ${load_addr:08x}"
    assert entry_pc == ENTRY_PC, f"entry PC mismatch: ${entry_pc:08x}"
    assert reset_sp == RESET_SP, f"reset SP mismatch: ${reset_sp:08x}"
    assert disk[80:80 + len(DISK_MARKER)] == DISK_MARKER, "disk marker missing"

    digest = sha256(payload).digest()
    assert disk[40:72] == digest, "payload SHA-256 manifest mismatch"
    embedded = disk[offset:offset + length]
    assert embedded == payload, "embedded WCS payload differs from standalone payload"

    sp, pc = struct.unpack_from(">II", payload, 0)
    assert sp == RESET_SP, f"payload reset SP mismatch: ${sp:08x}"
    assert pc == ENTRY_PC, f"payload entry PC mismatch: ${pc:08x}"
    assert payload[8:8 + len(CODE)] == CODE, "WCS diagnostic code mismatch"
    assert payload[0x100:0x100 + len(PAYLOAD_MARKER)] == PAYLOAD_MARKER, "WCS marker missing"

    print(f"A1000.2 static check PASS: {disk_path} ({len(disk)} bytes)")
    print(f"WCS payload={len(payload)} bytes load=${load_addr:08x} entry=${entry_pc:08x}")
    print(f"payload_sha256={sha256(payload).hexdigest()}")
    print("format=LibreKick-private bootstrap container; stock Kickstart-disk compatibility not claimed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
