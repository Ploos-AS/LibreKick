#!/usr/bin/env python3
"""Build LibreKick M2.2: first public exec.library LVO slice."""
from pathlib import Path
import struct, sys

ROM_SIZE = 512 * 1024
ROM_BASE = 0x00F80000
INITIAL_SP = 0x0007FFFC
RESET_PC = ROM_BASE + 8
EXEC_BASE = 0x00002200
COLOR00 = 0x00DFF180
CIAA_PRA = 0x00BFE001
CIAA_DDRA = 0x00BFE201
IDSTRING_ADDR = ROM_BASE + 0x180
FORBID_FUNC = ROM_BASE + 0x340
PERMIT_FUNC = ROM_BASE + 0x350
TDNEST_PRIVATE = 0x00001048


def ml(value, addr): return b"\x23\xfc" + struct.pack(">II", value, addr)
def mw(value, addr): return b"\x33\xfc" + struct.pack(">H", value) + struct.pack(">I", addr)
def mb(value, addr): return b"\x13\xfc" + struct.pack(">H", value & 0xff) + struct.pack(">I", addr)
def bclr0(addr): return bytes.fromhex("08B90000") + struct.pack(">I", addr)
def vector(target, addr):
    return ml(0x4EF90000 | ((target >> 16) & 0xffff), addr) + mw(target & 0xffff, addr + 4)

def ones_add32(total, value):
    total += value
    return (total & 0xffffffff) + (total >> 32)


def build():
    image = bytearray([0xff]) * ROM_SIZE
    struct.pack_into(">II", image, 0, INITIAL_SP, RESET_PC)

    c = bytearray()
    c += bytes.fromhex("46FC2700")
    c += mb(0x03, CIAA_DDRA)
    c += bclr0(CIAA_PRA)
    c += ml(EXEC_BASE, 4)

    # struct Library header. M2.2 only claims this header, not full ExecBase layout.
    c += ml(0, EXEC_BASE + 0)
    c += ml(0, EXEC_BASE + 4)
    c += mw(0x0900, EXEC_BASE + 8)
    c += ml(IDSTRING_ADDR, EXEC_BASE + 10)
    c += mw(0, EXEC_BASE + 14)
    c += mw(138, EXEC_BASE + 16)  # vectors through Permit(-138)
    c += mw(34, EXEC_BASE + 18)
    c += mw(40, EXEC_BASE + 20)
    c += mw(2, EXEC_BASE + 22)
    c += ml(IDSTRING_ADDR, EXEC_BASE + 24)
    c += ml(0, EXEC_BASE + 28)
    c += mw(0, EXEC_BASE + 32)

    # Public V40-compatible offsets used by existing Amiga software.
    c += vector(FORBID_FUNC, EXEC_BASE - 132)
    c += vector(PERMIT_FUNC, EXEC_BASE - 138)

    # Private backing state for the semantic probe: -1 means scheduling permitted.
    c += mb(0xff, TDNEST_PRIVATE)
    c += mw(0x0f00, COLOR00)  # red: about to exercise public LVOs
    c += b"\x4d\xf9" + struct.pack(">I", EXEC_BASE)
    c += bytes.fromhex("4EAEFF7C")  # jsr -132(a6) Forbid
    c += bytes.fromhex("4EAEFF7C")  # nested Forbid
    c += bytes.fromhex("4EAEFF76")  # Permit
    c += bytes.fromhex("0C390000") + struct.pack(">I", TDNEST_PRIVATE)  # cmpi.b #0,state
    bne_pos = len(c)
    c += bytes.fromhex("6600")  # patched short displacement
    c += mw(0x00f0, COLOR00)  # green: offsets, calls and nesting semantics passed
    bra_pos = len(c)
    c += bytes.fromhex("6000")
    fail_pos = len(c)
    c += mw(0x000f, COLOR00)  # blue: semantic probe failed
    idle_pos = len(c)
    c += bytes.fromhex("60FE")
    c[bne_pos + 1] = (fail_pos - (bne_pos + 2)) & 0xff
    c[bra_pos + 1] = (idle_pos - (bra_pos + 2)) & 0xff
    image[8:8+len(c)] = c

    image[0x100:0x100+len(b"LIBREKICK-M2.2\0PUBLIC-EXEC-LVO-FORBID-PERMIT\0")] = b"LIBREKICK-M2.2\0PUBLIC-EXEC-LVO-FORBID-PERMIT\0"
    ident = b"exec.library\0LibreKick M2.2 public LVO slice 40.2\0"
    image[0x180:0x180+len(ident)] = ident

    # Forbid: increment nesting byte. Permit: decrement. D/A registers untouched.
    image[0x340:0x346] = bytes.fromhex("523900001048")
    image[0x346:0x348] = bytes.fromhex("4E75")
    image[0x350:0x356] = bytes.fromhex("533900001048")
    image[0x356:0x358] = bytes.fromhex("4E75")

    struct.pack_into(">I", image, ROM_SIZE - 4, 0)
    total = 0
    for off in range(0, ROM_SIZE - 4, 4):
        total = ones_add32(total, struct.unpack_from(">I", image, off)[0])
    total = (total & 0xffffffff) + (total >> 32)
    struct.pack_into(">I", image, ROM_SIZE - 4, (~total) & 0xffffffff)
    return image

if __name__ == "__main__":
    if len(sys.argv) != 2: raise SystemExit("usage: make_m2_2_rom.py OUTPUT")
    out = Path(sys.argv[1]); data = build(); out.write_bytes(data)
    print(f"M2.2 ROM built: {out} ({len(data)} bytes)")
