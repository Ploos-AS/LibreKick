#!/usr/bin/env python3
from pathlib import Path
import struct, sys

ROM_SIZE = 512 * 1024
SP = 0x0007FFFC
PC = 0x00F80008
EXEC_BASE = 0x00002400
ADDHEAD = 0x00F80380
REMHEAD = 0x00F803A0
MARKER = b"LIBREKICK-M2.3\0PUBLIC-EXEC-LVO-ADDHEAD-REMHEAD\0"
IDENT = b"exec.library\0LibreKick M2.3 public list LVO slice 40.3\0"


def ones_add32(total, value):
    total += value
    return (total & 0xffffffff) + (total >> 32)


def vector_bytes(target):
    return bytes.fromhex("4EF9") + struct.pack(">I", target)

if len(sys.argv) != 2:
    raise SystemExit("usage: check_m2_3.py ROM")

p = Path(sys.argv[1]); data = p.read_bytes()
assert len(data) == ROM_SIZE, f"wrong ROM size: {len(data)}"
sp, pc = struct.unpack_from(">II", data, 0)
assert (sp, pc) == (SP, PC), f"bad reset vectors: {sp:08x} {pc:08x}"
assert data[0x100:0x100+len(MARKER)] == MARKER, "missing M2.3 marker"
assert data[0x180:0x180+len(IDENT)] == IDENT, "missing M2.3 identity"

# Public LVO slots are exact six-byte JMP absolute vectors.
add_slot = EXEC_BASE - 240
rem_slot = EXEC_BASE - 258
# These are RAM addresses at runtime; verify bootstrap contains the writes.
assert bytes.fromhex("23FC4EF900F8") in data[:0x180], "missing JMP vector writes"
assert struct.pack(">I", add_slot) in data[:0x180], "missing AddHead slot"
assert struct.pack(">I", rem_slot) in data[:0x180], "missing RemHead slot"
assert struct.pack(">H", ADDHEAD & 0xffff) in data[:0x180], "missing AddHead target"
assert struct.pack(">H", REMHEAD & 0xffff) in data[:0x180], "missing RemHead target"
assert bytes.fromhex("4EAEFF10") in data[:0x180], "missing AddHead call -240(a6)"
assert data[:0x180].count(bytes.fromhex("4EAEFEFE")) >= 2, "missing RemHead calls -258(a6)"

# Exact implementations placed in ROM.
ADDHEAD_CODE = bytes.fromhex(
    "2F002F082F092010228023480004204021490004206F00042089225F205F201F4E75"
)
REMHEAD_CODE = bytes.fromhex(
    "2F012F082F09201022402211670A208122412348000460027000225F205F221F4E75"
)
assert data[0x380:0x380+len(ADDHEAD_CODE)] == ADDHEAD_CODE, "AddHead implementation mismatch"
assert data[0x3A0:0x3A0+len(REMHEAD_CODE)] == REMHEAD_CODE, "RemHead implementation mismatch"

# Library header advertises enough negative vector space and V40.3 slice identity.
assert bytes.fromhex("33FC010200002410") in data[:0x180], "lib_NegSize != 258"
assert bytes.fromhex("33FC002800002414") in data[:0x180], "lib_Version != 40"
assert bytes.fromhex("33FC000300002416") in data[:0x180], "lib_Revision != 3"

# Runtime probe must include green success and blue failure markers.
assert bytes.fromhex("33FC00F000DFF180") in data[:0x180], "missing green PASS marker"
assert bytes.fromhex("33FC000F00DFF180") in data[:0x180], "missing blue FAIL marker"

sum32 = 0
for off in range(0, ROM_SIZE, 4):
    sum32 = ones_add32(sum32, struct.unpack_from(">I", data, off)[0])
sum32 = (sum32 & 0xffffffff) + (sum32 >> 32)
assert sum32 == 0xffffffff, f"bad ROM checksum: {sum32:08x}"

print(f"M2.3 check PASS: {p} ({len(data)} bytes)")
print("Exec AddHead(-240)/RemHead(-258); one-node + empty-list probe; checksum=0xffffffff")
