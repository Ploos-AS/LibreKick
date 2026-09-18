#!/usr/bin/env python3
"""Build a minimal stock-size A1000 boot-ROM execution probe."""
from pathlib import Path
import struct, sys

ROM_SIZE = 8192
RESET_SP = 0x0003FFFC
RESET_PC = 0x00F80008
COLOR00 = 0x00DFF180
# move.w #$0F00,$00DFF180 ; bra.s *
CODE = bytes.fromhex("33fc0f0000dff18060fe")

out = Path(sys.argv[1] if len(sys.argv)>1 else "build/a1000/librekick-a1000-probe.rom")
out.parent.mkdir(parents=True, exist_ok=True)
rom = bytearray([0xFF])*ROM_SIZE
struct.pack_into(">II", rom, 0, RESET_SP, RESET_PC)
rom[8:8+len(CODE)] = CODE
rom[0x100:0x100+len(b"LIBREKICK-A1000-PROBE\0")] = b"LIBREKICK-A1000-PROBE\0"
out.write_bytes(rom)
print(f"A1000 probe ROM built: {out} ({len(rom)} bytes)")
