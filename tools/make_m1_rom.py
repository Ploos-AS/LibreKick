#!/usr/bin/env python3
"""Build the first bootable LibreKick M1 512 KiB ROM image.

The image contains only a tiny 68000 reset/bootstrap stub. It is intentionally
not an AmigaOS-compatible kernel yet; M1 proves reset-vector execution and a
repeatable ROM layout before higher-level components are introduced.
"""
from pathlib import Path
import struct
import sys

ROM_SIZE = 512 * 1024
ROM_BASE = 0x00F80000
INITIAL_SP = 0x0007FFFC
RESET_PC = ROM_BASE + 8
DEBUG_SIGNATURE_ADDR = 0x00001000
DEBUG_SIGNATURE = 0x4C4B3031  # "LK01"
COLOR00 = 0x00DFF180


def ones_add32(total: int, value: int) -> int:
    total += value
    return (total & 0xFFFFFFFF) + (total >> 32)


def build() -> bytearray:
    image = bytearray([0xFF]) * ROM_SIZE

    # Reset vectors while ROM overlay is visible at address 0.
    struct.pack_into(">II", image, 0, INITIAL_SP, RESET_PC)

    # 68000 bootstrap at ROM_BASE + 8:
    #   move.w  #$2700,sr                 ; supervisor, interrupts masked
    #   move.l  #$4c4b3031,$00001000      ; chip-RAM signature "LK01"
    #   move.w  #$000f,$00dff180          ; visible COLOR00 marker
    # loop:
    #   bra.s   loop
    code = bytes.fromhex(
        "46FC2700"
        "23FC4C4B303100001000"
        "33FC000F00DFF180"
        "60FE"
    )
    image[8:8 + len(code)] = code

    marker = b"LIBREKICK-M1\0BOOTSTRAP-68000\0"
    image[0x40:0x40 + len(marker)] = marker

    # Reserve final longword for a deterministic one's-complement ROM checksum.
    struct.pack_into(">I", image, ROM_SIZE - 4, 0)
    total = 0
    for offset in range(0, ROM_SIZE - 4, 4):
        total = ones_add32(total, struct.unpack_from(">I", image, offset)[0])
    total = (total & 0xFFFFFFFF) + (total >> 32)
    correction = (~total) & 0xFFFFFFFF
    struct.pack_into(">I", image, ROM_SIZE - 4, correction)
    return image


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: make_m1_rom.py OUTPUT")
    out = Path(sys.argv[1])
    image = build()
    out.write_bytes(image)
    print(f"M1 ROM built: {out} ({len(image)} bytes)")


if __name__ == "__main__":
    main()
