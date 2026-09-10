#!/usr/bin/env python3
from pathlib import Path
import struct, sys

ROM_SIZE = 512 * 1024
MARKER = b"LIBREKICK-M2.2\0PUBLIC-EXEC-LVO-FORBID-PERMIT\0"
IDENT = b"exec.library\0LibreKick M2.2 public LVO slice 40.2\0"
EXPECTED_SP = 0x0007FFFC
EXPECTED_PC = 0x00F80008


def ones_add32(total, value):
    total += value
    return (total & 0xffffffff) + (total >> 32)

if len(sys.argv) != 2:
    raise SystemExit("usage: check_m2_2.py ROM")

p = Path(sys.argv[1]); data = p.read_bytes()
assert len(data) == ROM_SIZE
sp, pc = struct.unpack_from(">II", data, 0)
assert sp == EXPECTED_SP and pc == EXPECTED_PC
assert data[0x100:0x100+len(MARKER)] == MARKER
assert data[0x180:0x180+len(IDENT)] == IDENT

required = [
    bytes.fromhex("13FC000300BFE201"),      # DDRA output
    bytes.fromhex("08B9000000BFE001"),      # OVL off
    bytes.fromhex("23FC0000220000000004"),  # SysBase
    bytes.fromhex("33FC008A00002210"),      # lib_NegSize=138
    bytes.fromhex("33FC002800002214"),      # version 40
    bytes.fromhex("33FC000200002216"),      # revision 2
    bytes.fromhex("4EAEFF7C4EAEFF7C4EAEFF76"), # Forbid, Forbid, Permit
    bytes.fromhex("0C39000000001048"),      # nesting probe
    bytes.fromhex("33FC00F000DFF180"),      # green success
]
for blob in required:
    assert blob in data[:0x240], f"missing sequence: {blob.hex()}"

# Vector slots are six-byte JMP absolute entries.
assert data[0x340:0x348] == bytes.fromhex("5239000010484E75")
assert data[0x350:0x358] == bytes.fromhex("5339000010484E75")

# The generator must embed absolute targets for public LVOs in bootstrap writes.
assert bytes.fromhex("23FC4EF900F80000217C33FC034000002180") in data[:0x240]
assert bytes.fromhex("23FC4EF900F80000217633FC03500000217A") in data[:0x240]

total = 0
for off in range(0, ROM_SIZE, 4):
    total = ones_add32(total, struct.unpack_from(">I", data, off)[0])
total = (total & 0xffffffff) + (total >> 32)
assert total == 0xffffffff, hex(total)
print(f"M2.2 check PASS: {p} ({len(data)} bytes)")
print(f"reset SP=0x{sp:08x} PC=0x{pc:08x}; Forbid=-132 Permit=-138; checksum=0x{total:08x}")
