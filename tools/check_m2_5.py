#!/usr/bin/env python3
from pathlib import Path
import struct, sys

ROM_SIZE = 512 * 1024
SP = 0x0007FFFC
PC = 0x00F80008
EXEC_BASE = 0x00002C00
MARKER_OFF = 0x1200
IDENT_OFF = 0x1280
MARKER = b"LIBREKICK-M2.5\0EXEC-QUEUE-FINDNAME\0"
IDENT = b"exec.library\0LibreKick M2.5 complete classic list slice 40.5\0"
BOOTSTRAP_END = 0x0800

FUNCS = {
    234: 0x0800, 240: 0x0840, 246: 0x0880, 252: 0x08C0,
    258: 0x0900, 264: 0x0940, 270: 0x0A00, 276: 0x0A80,
}

def ones_add32(total, value):
    total += value
    return (total & 0xffffffff) + (total >> 32)

def branch_word_target(data, opcode_off):
    disp = struct.unpack_from(">h", data, opcode_off + 2)[0]
    # Motorola 68000 Bcc.W/BRA.W uses PC = opcode address + 2.
    return opcode_off + 2 + disp

if len(sys.argv) != 2:
    raise SystemExit("usage: check_m2_5.py ROM")

p = Path(sys.argv[1]); data = p.read_bytes()
assert len(data) == ROM_SIZE, f"wrong ROM size: {len(data)}"
sp, pc = struct.unpack_from(">II", data, 0)
assert (sp, pc) == (SP, PC), f"bad reset vectors: {sp:08x} {pc:08x}"
assert data[MARKER_OFF:MARKER_OFF+len(MARKER)] == MARKER, "missing M2.5 marker"
assert data[IDENT_OFF:IDENT_OFF+len(IDENT)] == IDENT, "missing M2.5 identity"
boot = data[8:BOOTSTRAP_END]

assert bytes.fromhex("13FC000300BFE201") in boot, "missing CIAA DDRA setup"
assert bytes.fromhex("08B9000000BFE001") in boot, "missing OVL clear"
assert bytes.fromhex("23FC00002C0000000004") in boot, "SysBase != $2c00"
assert bytes.fromhex("33FC011400002C10") in boot, "lib_NegSize != 276"
assert bytes.fromhex("33FC002800002C14") in boot, "lib_Version != 40"
assert bytes.fromhex("33FC000500002C16") in boot, "lib_Revision != 5"

for lvo, rom_off in FUNCS.items():
    slot = EXEC_BASE - lvo
    target = 0x00F80000 + rom_off
    assert struct.pack(">I", slot) in boot, f"missing LVO -{lvo} slot write"
    assert struct.pack(">H", target & 0xffff) in boot, f"missing LVO -{lvo} target"
    assert data[rom_off:rom_off+2] != b"\xff\xff", f"LVO -{lvo} routine missing"

assert boot.count(bytes.fromhex("4EAEFEF2")) == 3, "Enqueue -270 must be called three times"
assert boot.count(bytes.fromhex("4EAEFEEC")) == 5, "FindName -276 must be called five times"
assert bytes.fromhex("4EAEFF16") in data[0x0A00:0x0A80], "Enqueue must delegate insertion through Insert -234"
assert bytes.fromhex("4A8A") not in data[0x0800:0x0B00], "illegal TST.L A2 regression on 68000"
assert bytes.fromhex("33FC00F000DFF180") in boot, "missing green PASS marker"
assert bytes.fromhex("33FC000F00DFF180") in boot, "missing blue FAIL marker"

# Regression for the M2.5 branch bug: locate the sentinel TST/BEQ inside
# Enqueue and require the word branch to land exactly on the insert path.
enqueue = data[0x0A00:0x0A80]
needle = bytes.fromhex("4A806700")
idx = enqueue.find(needle)
assert idx >= 0, "missing Enqueue sentinel TST.L D0 / BEQ.W"
beq_off = 0x0A00 + idx + 2
target = branch_word_target(data, beq_off)
assert data[target:target+10] == bytes.fromhex("244B33FC0F0F00DFF180"), (
    f"Enqueue sentinel BEQ target wrong: 0x{target:04x}"
)

assert data[0x1400:0x1406] == b"alpha\0"
assert data[0x1410:0x1415] == b"beta\0"
assert data[0x1420:0x1428] == b"missing\0"

sum32 = 0
for off in range(0, ROM_SIZE, 4):
    sum32 = ones_add32(sum32, struct.unpack_from(">I", data, off)[0])
sum32 = (sum32 & 0xffffffff) + (sum32 >> 32)
assert sum32 == 0xffffffff, f"bad ROM checksum: {sum32:08x}"

print(f"M2.5 check PASS: {p} ({len(data)} bytes)")
print("Exec Enqueue(-270)/FindName(-276); corrected 68000 Bcc.W PC base; checksum=0xffffffff")
