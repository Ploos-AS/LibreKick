#!/usr/bin/env python3
"""Static validation for the LibreKick A1000.3 DF0 -> WCS bootstrap loader."""
from __future__ import annotations

from pathlib import Path
import struct
import sys

ROM_SIZE = 64 * 1024
RESET_SP = 0x0003FFFC
BOOT_BASE = 0x00F80000
MARKER = b"LIBREKICK-A1000.3\0DF0-WCS-LOADER\0"


def main() -> int:
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "build/a1000/librekick-a1000.3-bootstrap.rom")
    data = path.read_bytes()
    assert len(data) == ROM_SIZE, f"size: expected {ROM_SIZE}, got {len(data)}"

    sp, pc = struct.unpack_from(">II", data, 0)
    assert sp == RESET_SP, f"reset SP mismatch: ${sp:08x}"
    assert BOOT_BASE <= pc < BOOT_BASE + ROM_SIZE, f"reset PC outside bootstrap: ${pc:08x}"
    assert MARKER in data, "A1000.3 loader marker missing"

    # Constants used by the generated FS-UAE runtime image must be present in
    # the final binary. /RDY and track-zero polling are bypassed by the
    # emulator overlay, but CIA-A PRA/DDRA must remain because reset OVL must
    # be released before the bootstrap can use low Chip RAM.
    for value, name in [
        (0x00FC0000, "WCS base"),
        (0x00FC0008, "WCS entry"),
        (0x00DFF020, "DSKPTH"),
        (0x00DFF024, "DSKLEN"),
        (0x00DFF07E, "DSKSYNC"),
        (0x00DFF096, "DMACON"),
        (0x00DFF09E, "ADKCON"),
        (0x00BFD100, "CIAB PRB"),
        (0x00BFE001, "CIAA PRA / OVL"),
        (0x00BFE201, "CIAA DDRA"),
    ]:
        needle = struct.pack(">I", value)
        assert needle in data, f"missing {name} constant ${value:08x}"

    assert b"\x44\x89" in data, "MFM sync word 0x4489 missing"
    assert b"\x55\x55\x55\x55" in data, "MFM decode mask missing"

    print(f"A1000.3 static check PASS: {path} ({len(data)} bytes)")
    print(f"reset_sp=${sp:08x} reset_pc=${pc:08x}")
    print("scope=OVL release + DF0 standard-MFM sector loader + private manifest + 256KiB WCS handoff")
    print("runtime overlay bypasses /RDY and track-zero sensing; hardware qualification is separate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
