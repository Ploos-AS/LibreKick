#!/usr/bin/env python3
"""Build LibreKick M2.0: first Exec-shaped bootstrap foundation.

M2.0 is intentionally not a complete exec.library implementation. It proves
that LibreKick can establish the canonical SysBase pointer at address 4 and a
stable in-RAM kernel descriptor before later M2 slices add real Exec ABI
structures and callable functions.
"""
from pathlib import Path
import struct
import sys

ROM_SIZE = 512 * 1024
ROM_BASE = 0x00F80000
INITIAL_SP = 0x0007FFFC
RESET_PC = ROM_BASE + 8
SYSBASE_PTR_ADDR = 0x00000004
SYSBASE = 0x00002000
COLOR00 = 0x00DFF180
SIGNATURE = 0x45583031  # EX01


def ones_add32(total: int, value: int) -> int:
    total += value
    return (total & 0xFFFFFFFF) + (total >> 32)


def build() -> bytearray:
    image = bytearray([0xFF]) * ROM_SIZE
    struct.pack_into(">II", image, 0, INITIAL_SP, RESET_PC)

    # 68000 bootstrap:
    #   move.w #$2700,sr
    #   move.l #$00002000,$00000004     ; canonical SysBase pointer location
    #   move.l #$45583031,$00002000     ; "EX01" descriptor signature
    #   move.w #$0028,$00002004         ; target major version 40
    #   move.w #$0000,$00002006         ; revision 0
    #   move.l #$00000400,$00002008     ; bootstrap-reserved low RAM end
    #   move.l #$0007fffc,$0000200c     ; initial top-of-RAM marker
    #   move.w #$00f0,$00dff180         ; green M2 runtime marker
    # loop: bra.s loop
    code = bytes.fromhex(
        "46FC2700"
        "23FC0000200000000004"
        "23FC4558303100002000"
        "33FC002800002004"
        "33FC000000002006"
        "23FC0000040000002008"
        "23FC0007FFFC0000200C"
        "33FC00F000DFF180"
        "60FE"
    )
    image[8:8 + len(code)] = code

    marker = b"LIBREKICK-M2.0\0EXEC-FOUNDATION-68000\0"
    image[0x80:0x80 + len(marker)] = marker

    struct.pack_into(">I", image, ROM_SIZE - 4, 0)
    total = 0
    for offset in range(0, ROM_SIZE - 4, 4):
        total = ones_add32(total, struct.unpack_from(">I", image, offset)[0])
    total = (total & 0xFFFFFFFF) + (total >> 32)
    struct.pack_into(">I", image, ROM_SIZE - 4, (~total) & 0xFFFFFFFF)
    return image


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: make_m2_rom.py OUTPUT")
    out = Path(sys.argv[1])
    out.parent.mkdir(parents=True, exist_ok=True)
    image = build()
    out.write_bytes(image)
    print(f"M2.0 ROM built: {out} ({len(image)} bytes)")


if __name__ == "__main__":
    main()
