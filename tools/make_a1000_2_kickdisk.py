#!/usr/bin/env python3
"""Build the deterministic LibreKick A1000.4 WCS diagnostic payload and disk.

The private disk-container format remains version 2; A1000.4 advances the
payload milestone, not the on-disk manifest ABI.  The image is an 880 KiB
ADF-geometry image with its manifest in sector 0 and the complete 256 KiB WCS
payload beginning at sector 1.
"""
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
PAYLOAD_MARKER = b"LIBREKICK-A1000.4\0WCS-DIAGNOSTIC\0"
DISK_MARKER = b"LIBREKICK-A1000.4\0KICKDISK-CONTAINER\0"


def build_payload() -> bytes:
    payload = bytearray(WCS_SIZE)
    struct.pack_into(">II", payload, 0, RESET_SP, ENTRY_PC)
    # First native WCS-resident diagnostic runtime:
    # MOVE.W #$00f0,$00dff180 ; BRA.S .
    # Reaching this code proves that the bootstrap populated WCS and handed
    # execution to the payload entry point.
    code = bytes.fromhex("33fc00f000dff18060fe")
    payload[8:8 + len(code)] = code
    payload[0x100:0x100 + len(PAYLOAD_MARKER)] = PAYLOAD_MARKER
    return bytes(payload)


def build_disk(payload: bytes) -> bytes:
    image = bytearray(ADF_SIZE)
    digest = sha256(payload).digest()
    image[0:len(MAGIC)] = MAGIC
    struct.pack_into(">IIIIII", image, 16,
                     FORMAT_VERSION,
                     PAYLOAD_OFFSET,
                     len(payload),
                     WCS_BASE,
                     ENTRY_PC,
                     RESET_SP)
    image[40:72] = digest
    image[80:80 + len(DISK_MARKER)] = DISK_MARKER
    image[PAYLOAD_OFFSET:PAYLOAD_OFFSET + len(payload)] = payload
    return bytes(image)


def main() -> int:
    out_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "build/a1000")
    out_dir.mkdir(parents=True, exist_ok=True)
    payload_path = out_dir / "librekick-a1000.4-wcs.bin"
    disk_path = out_dir / "librekick-a1000.4-kickdisk.adf"

    payload = build_payload()
    disk = build_disk(payload)
    payload_path.write_bytes(payload)
    disk_path.write_bytes(disk)

    print(f"A1000.4 WCS payload built: {payload_path} ({len(payload)} bytes)")
    print(f"A1000.4 kickdisk built: {disk_path} ({len(disk)} bytes)")
    print(f"wcs_base=${WCS_BASE:08x} entry_pc=${ENTRY_PC:08x} payload_sha256={sha256(payload).hexdigest()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
