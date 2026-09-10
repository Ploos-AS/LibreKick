#!/usr/bin/env python3
from pathlib import Path
import struct
import sys

ROM_SIZE = 512 * 1024
EXPECTED_SP = 0x0007FFFC
EXPECTED_PC = 0x00F80008
MARKER = b"LIBREKICK-M2.1\0LIBRARY-ABI-VECTOR-FOUNDATION\0"
IDENT = b"exec.library\0LibreKick M2.1 ABI foundation 40.1\0"
PROBE = bytes.fromhex("203C4C4B56314E75")


def ones_add32(total: int, value: int) -> int:
    total += value
    return (total & 0xFFFFFFFF) + (total >> 32)


if len(sys.argv) != 2:
    raise SystemExit("usage: check_m2_1.py ROM")

p = Path(sys.argv[1])
data = p.read_bytes()
assert len(data) == ROM_SIZE, f"wrong ROM size: {len(data)}"
sp, pc = struct.unpack_from(">II", data, 0)
assert sp == EXPECTED_SP, f"wrong reset SP: 0x{sp:08x}"
assert pc == EXPECTED_PC, f"wrong reset PC: 0x{pc:08x}"
assert data[0x100:0x100 + len(MARKER)] == MARKER, "missing M2.1 marker"
assert data[0x180:0x180 + len(IDENT)] == IDENT, "missing exec.library identity"
assert data[0x300:0x300 + len(PROBE)] == PROBE, "probe function mismatch"

# Required bootstrap evidence encoded in the ROM.
required = [
    bytes.fromhex("23FC0000210000000004"),  # SysBase -> $2100
    bytes.fromhex("33FC000600002110"),      # lib_NegSize = 6
    bytes.fromhex("33FC002200002112"),      # lib_PosSize = 34
    bytes.fromhex("33FC002800002114"),      # version 40
    bytes.fromhex("33FC000100002116"),      # revision 1
    bytes.fromhex("23FC4EF900F8000020FA"),  # vector JMP prefix at base-6
    bytes.fromhex("33FC0300000020FE"),      # vector target low word -> $f80300
    bytes.fromhex("4DF9000021004EAEFFFA"),  # lea base,a6; jsr -6(a6)
    bytes.fromhex("23C000001040"),          # result d0 -> $1040
    bytes.fromhex("33FC0F0F00DFF180"),      # magenta runtime marker
]
for blob in required:
    assert blob in data[:0x180], f"missing bootstrap sequence {blob.hex()}"

total = 0
for off in range(0, ROM_SIZE, 4):
    total = ones_add32(total, struct.unpack_from(">I", data, off)[0])
total = (total & 0xFFFFFFFF) + (total >> 32)
assert total == 0xFFFFFFFF, f"bad ROM checksum: 0x{total:08x}"

print(f"M2.1 check PASS: {p} ({len(data)} bytes)")
print(f"reset SP=0x{sp:08x} PC=0x{pc:08x}; SysBase->$00002100; vector=-6(a6); checksum=0x{total:08x}")
