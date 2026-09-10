#!/usr/bin/env python3
from pathlib import Path
import struct, sys

ROM_SIZE = 512 * 1024
SP = 0x0007FFFC
PC = 0x00F80008
EXEC_BASE = 0x00002800
MARKER_OFF = 0x1000
IDENT_OFF = 0x1080
MARKER = b"LIBREKICK-M2.4\0EXEC-BASIC-LIST-API\0"
IDENT = b"exec.library\0LibreKick M2.4 basic list API 40.4\0"
BOOTSTRAP_END = 0x0800

FUNCS = {
    234: (0x0800, bytes.fromhex(
        "2F002F082F092F0A200A4A80671220122280234A000420402149000424896010"
        "20102280234800042440254900042089245F225F205F201F4E75"
    )),
    240: (0x0840, bytes.fromhex(
        "2F002F082F092010228023480004204021490004206F00042089225F205F201F4E75"
    )),
    246: (0x0880, bytes.fromhex(
        "2F002F082F092028000841E8000422882340000420402089206F000421490008225F205F201F4E75"
    )),
    252: (0x08C0, bytes.fromhex(
        "2F002F012F082F0920290004221120402081204121400004225F205F221F201F4E75"
    )),
    258: (0x0900, bytes.fromhex(
        "2F012F082F09201022402211670A208122412348000460027000225F205F221F4E75"
    )),
    264: (0x0940, bytes.fromhex(
        "2F012F082F0920280008224022290004670E21410008224141E80004228860027000225F205F221F4E75"
    )),
}


def ones_add32(total, value):
    total += value
    return (total & 0xffffffff) + (total >> 32)

if len(sys.argv) != 2:
    raise SystemExit("usage: check_m2_4.py ROM")

p = Path(sys.argv[1]); data = p.read_bytes()
assert len(data) == ROM_SIZE, f"wrong ROM size: {len(data)}"
sp, pc = struct.unpack_from(">II", data, 0)
assert (sp, pc) == (SP, PC), f"bad reset vectors: {sp:08x} {pc:08x}"
assert data[MARKER_OFF:MARKER_OFF+len(MARKER)] == MARKER, "missing M2.4 marker"
assert data[IDENT_OFF:IDENT_OFF+len(IDENT)] == IDENT, "missing M2.4 identity"
boot = data[8:BOOTSTRAP_END]

assert bytes.fromhex("13FC000300BFE201") in boot, "missing CIAA DDRA setup"
assert bytes.fromhex("08B9000000BFE001") in boot, "missing OVL clear"
assert bytes.fromhex("23FC0000280000000004") in boot, "SysBase != $2800"
assert bytes.fromhex("33FC010800002810") in boot, "lib_NegSize != 264"
assert bytes.fromhex("33FC002800002814") in boot, "lib_Version != 40"
assert bytes.fromhex("33FC000400002816") in boot, "lib_Revision != 4"

for offset, (rom_off, code) in FUNCS.items():
    slot = EXEC_BASE - offset
    target = 0x00F80000 + rom_off
    assert struct.pack(">I", slot) in boot, f"missing LVO -{offset} slot write"
    assert struct.pack(">H", target & 0xffff) in boot, f"missing LVO -{offset} target"
    got = data[rom_off:rom_off+len(code)]
    assert got == code, f"LVO -{offset} implementation mismatch: got {got.hex()}"

# 68000 safety regression: TST.L An is illegal. Insert must copy A2 to D0 first.
assert bytes.fromhex("200A4A80") in FUNCS[234][1], "Insert NULL test is not 68000-safe"
assert bytes.fromhex("4A8A") not in FUNCS[234][1], "illegal TST.L A2 remains in Insert"

assert boot.count(bytes.fromhex("4EAEFF16")) >= 2, "Insert -234 not exercised twice"
assert boot.count(bytes.fromhex("4EAEFF0A")) >= 2, "AddTail -246 not exercised twice"
assert bytes.fromhex("4EAEFF04") in boot, "Remove -252 not exercised"
assert boot.count(bytes.fromhex("4EAEFEF8")) >= 3, "RemTail -264 not exercised three times"
assert boot.count(bytes.fromhex("4EAEFEFE")) >= 2, "RemHead regression cleanup missing"
assert bytes.fromhex("247C00000000") in boot, "Insert NULL-predecessor case missing"
assert bytes.fromhex("33FC00F000DFF180") in boot, "missing green PASS marker"
assert bytes.fromhex("33FC000F00DFF180") in boot, "missing blue FAIL marker"

ordered = sorted((rom_off, len(code), offset) for offset, (rom_off, code) in FUNCS.items())
for (off, size, lvo), (next_off, _, _) in zip(ordered, ordered[1:]):
    assert off + size <= next_off, f"LVO -{lvo} routine overlaps next routine"
assert ordered[-1][0] + ordered[-1][1] <= MARKER_OFF, "routine overlaps metadata"

sum32 = 0
for off in range(0, ROM_SIZE, 4):
    sum32 = ones_add32(sum32, struct.unpack_from(">I", data, off)[0])
sum32 = (sum32 & 0xffffffff) + (sum32 >> 32)
assert sum32 == 0xffffffff, f"bad ROM checksum: {sum32:08x}"

print(f"M2.4b check PASS: {p} ({len(data)} bytes)")
print("Exec Insert/AddHead/AddTail/Remove/RemHead/RemTail; 68000-safe Insert; checksum=0xffffffff")
