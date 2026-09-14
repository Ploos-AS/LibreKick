#!/usr/bin/env python3
"""Static checker for the clean-room LibreKick A1000.0 bootstrap ROM skeleton."""
from __future__ import annotations

from pathlib import Path
import struct
import sys

ROM_SIZE = 64 * 1024
RESET_SP = 0x0007FFFC
BOOT_BASE = 0x00FC0000
RESET_PC = BOOT_BASE + 8
MARKER = b"LIBREKICK-A1000.0\0BOOTSTRAP-SKELETON\0"
CODE = bytes.fromhex("33fc00f000dff18060fe")


def main() -> int:
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "build/a1000/librekick-a1000.0-bootstrap.rom")
    data = path.read_bytes()
    assert len(data) == ROM_SIZE, f"size: expected {ROM_SIZE}, got {len(data)}"

    sp, pc = struct.unpack_from(">II", data, 0)
    assert sp == RESET_SP, f"reset SP mismatch: ${sp:08x}"
    assert pc == RESET_PC, f"reset PC mismatch: ${pc:08x}"
    assert data[8:8 + len(CODE)] == CODE, "bootstrap marker code mismatch"
    assert data[0x100:0x100 + len(MARKER)] == MARKER, "A1000.0 marker missing"

    # A1000.0 intentionally does not pretend to be a normal Kickstart ROM.
    # Therefore no standard 512 KiB Kickstart checksum assertion belongs here.
    print(f"A1000.0 static check PASS: {path} ({len(data)} bytes)")
    print(f"reset_sp=${sp:08x} reset_pc=${pc:08x}; WCS loader not implemented")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
