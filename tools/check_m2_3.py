#!/usr/bin/env python3
from pathlib import Path
import struct, sys

ROM_SIZE = 512 * 1024
SP = 0x0007FFFC
PC = 0x00F80008
EXEC_BASE = 0x00002400
ADDHEAD = 0x00F80380
REMHEAD = 0x00F803A0
MARKER_OFF = 0x500
IDENT_OFF = 0x580
MARKER = b"LIBREKICK-M2.3\0PUBLIC-EXEC-LVO-ADDHEAD-REMHEAD\0"
IDENT = b"exec.library\0LibreKick M2.3 public list LVO slice 40.3\0"
BOOTSTRAP_END = 0x300


def ones_add32(total, value):
    total += value
    return (total & 0xffffffff) + (total >> 32)

if len(sys.argv) != 2:
    raise SystemExit("usage: check_m2_3.py ROM")

p = Path(sys.argv[1]); data = p.read_bytes()
assert len(data) == ROM_SIZE, f"wrong ROM size: {len(data)}"
sp, pc = struct.unpack_from(">II", data, 0)
assert (sp, pc) == (SP, PC), f"bad reset vectors: {sp:08x} {pc:08x}"
assert data[MARKER_OFF:MARKER_OFF+len(MARKER)] == MARKER, "missing M2.3 marker"
assert data[IDENT_OFF:IDENT_OFF+len(IDENT)] == IDENT, "missing M2.3 identity"
boot = data[8:BOOTSTRAP_END]

add_slot = EXEC_BASE - 240
rem_slot = EXEC_BASE - 258
assert bytes.fromhex("23FC4EF900F8") in boot, "missing JMP vector writes"
assert struct.pack(">I", add_slot) in boot, "missing AddHead slot"
assert struct.pack(">I", rem_slot) in boot, "missing RemHead slot"
assert struct.pack(">H", ADDHEAD & 0xffff) in boot, "missing AddHead target"
assert struct.pack(">H", REMHEAD & 0xffff) in boot, "missing RemHead target"
assert bytes.fromhex("4EAEFF10") in boot, "missing AddHead call -240(a6)"
assert boot.count(bytes.fromhex("4EAEFEFE")) >= 2, "missing RemHead calls -258(a6)"

# Keep the static checker byte-for-byte aligned with the generator. The M2.3
# qualification validates the exact emitted routines, not a separately copied
# hand-assembly variant.
ADDHEAD_CODE = bytes.fromhex(
    "2F002F082F092010228023480004204021490004206F00042089225F205F201F4E75"
)
REMHEAD_CODE = bytes.fromhex(
    "2F012F082F09201022402211670A208122412348000460027000225F205F221F4E75"
)
assert data[0x380:0x380+len(ADDHEAD_CODE)] == ADDHEAD_CODE, (
    f"AddHead implementation mismatch: got {data[0x380:0x380+len(ADDHEAD_CODE)].hex()}"
)
assert data[0x3A0:0x3A0+len(REMHEAD_CODE)] == REMHEAD_CODE, (
    f"RemHead implementation mismatch: got {data[0x3A0:0x3A0+len(REMHEAD_CODE)].hex()}"
)

assert bytes.fromhex("33FC010200002410") in boot, "lib_NegSize != 258"
assert bytes.fromhex("33FC002800002414") in boot, "lib_Version != 40"
assert bytes.fromhex("33FC000300002416") in boot, "lib_Revision != 3"
assert bytes.fromhex("33FC00F000DFF180") in boot, "missing green PASS marker"
assert bytes.fromhex("33FC000F00DFF180") in boot, "missing blue FAIL marker"

sum32 = 0
for off in range(0, ROM_SIZE, 4):
    sum32 = ones_add32(sum32, struct.unpack_from(">I", data, off)[0])
sum32 = (sum32 & 0xffffffff) + (sum32 >> 32)
assert sum32 == 0xffffffff, f"bad ROM checksum: {sum32:08x}"

print(f"M2.3 check PASS: {p} ({len(data)} bytes)")
print("Exec AddHead(-240)/RemHead(-258); one-node + empty-list probe; checksum=0xffffffff")
