#!/usr/bin/env python3
"""Generate the clean-room LibreKick A1000 bootstrap ROM skeleton.

This is deliberately a bootstrap-ROM artifact, not a 512 KiB Kickstart image and
not yet a WCS loader.  FS-UAE/UAE maps the A1000 bootstrap ROM into the lower
256 KiB half of Kick memory (starting at $F80000) while the upper 256 KiB is WCS.
Small bootstrap images are mirrored across that lower half by the emulator.
"""
from __future__ import annotations

from pathlib import Path
import struct
import sys

ROM_SIZE = 64 * 1024
RESET_SP = 0x0007FFFC
BOOT_BASE = 0x00F80000
RESET_PC = BOOT_BASE + 8
COLOR00 = 0x00DFF180
PASS_COLOR = 0x00F0
MARKER = b"LIBREKICK-A1000.1\0BOOTSTRAP-RUNTIME-MAP\0"


def main() -> int:
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "build/a1000/librekick-a1000.1-bootstrap.rom")
    out.parent.mkdir(parents=True, exist_ok=True)

    rom = bytearray([0xFF]) * ROM_SIZE
    struct.pack_into(">II", rom, 0, RESET_SP, RESET_PC)

    # 68000 runtime marker at reset entry:
    #   MOVE.W #$00f0,$00dff180
    # .hang:
    #   BRA.S .hang
    code = bytes.fromhex("33fc00f000dff18060fe")
    rom[8:8 + len(code)] = code
    rom[0x100:0x100 + len(MARKER)] = MARKER

    out.write_bytes(rom)
    print(f"A1000.1 bootstrap ROM built: {out} ({len(rom)} bytes)")
    print(f"reset_sp=${RESET_SP:08x} reset_pc=${RESET_PC:08x} boot_base=${BOOT_BASE:08x}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
