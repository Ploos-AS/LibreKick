#!/usr/bin/env python3
from pathlib import Path
import struct
import sys

ROM_SIZE = 512 * 1024
EXPECTED_SP = 0x0007FFFC
EXPECTED_PC = 0x00F80008
MARKER = b"LIBREKICK-M2.0\0EXEC-FOUNDATION-68000\0"
EXPECTED_CODE = bytes.fromhex(
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


def ones_add32(total: int, value: int) -> int:
    total += value
    return (total & 0xFFFFFFFF) + (total >> 32)


if len(sys.argv) != 2:
    raise SystemExit("usage: check_m2.py ROM")

p = Path(sys.argv[1])
data = p.read_bytes()
assert len(data) == ROM_SIZE, f"wrong ROM size: {len(data)}"
sp, pc = struct.unpack_from(">II", data, 0)
assert sp == EXPECTED_SP, f"wrong reset SP: 0x{sp:08x}"
assert pc == EXPECTED_PC, f"wrong reset PC: 0x{pc:08x}"
assert data[8:8 + len(EXPECTED_CODE)] == EXPECTED_CODE, "M2 bootstrap mismatch"
assert data[0x80:0x80 + len(MARKER)] == MARKER, "missing M2 marker"

total = 0
for off in range(0, ROM_SIZE, 4):
    total = ones_add32(total, struct.unpack_from(">I", data, off)[0])
total = (total & 0xFFFFFFFF) + (total >> 32)
assert total == 0xFFFFFFFF, f"bad ROM checksum: 0x{total:08x}"

print(f"M2.0 check PASS: {p} ({len(data)} bytes)")
print(f"reset SP=0x{sp:08x} PC=0x{pc:08x}; SysBase->$00002000; checksum=0x{total:08x}")
