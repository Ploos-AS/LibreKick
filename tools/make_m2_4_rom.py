#!/usr/bin/env python3
"""Build LibreKick M2.4b: complete basic Exec list API with runtime checkpoints."""
from pathlib import Path
import struct, sys

ROM_SIZE = 512 * 1024
ROM_BASE = 0x00F80000
INITIAL_SP = 0x0007FFFC
RESET_PC = ROM_BASE + 8
EXEC_BASE = 0x00002800
COLOR00 = 0x00DFF180
CIAA_PRA = 0x00BFE001
CIAA_DDRA = 0x00BFE201
MARKER_OFF = 0x1000
IDENT_OFF = 0x1080
IDSTRING_ADDR = ROM_BASE + IDENT_OFF
LIST_ADDR = 0x00001100
NODE1 = 0x00001120
NODE2 = 0x00001140
NODE3 = 0x00001160

INSERT_FUNC = ROM_BASE + 0x0800
ADDHEAD_FUNC = ROM_BASE + 0x0840
ADDTAIL_FUNC = ROM_BASE + 0x0880
REMOVE_FUNC = ROM_BASE + 0x08C0
REMHEAD_FUNC = ROM_BASE + 0x0900
REMTAIL_FUNC = ROM_BASE + 0x0940


def ml(value, addr): return b"\x23\xfc" + struct.pack(">II", value, addr)
def mw(value, addr): return b"\x33\xfc" + struct.pack(">H", value) + struct.pack(">I", addr)
def mb(value, addr): return b"\x13\xfc" + struct.pack(">H", value & 0xff) + struct.pack(">I", addr)
def bclr0(addr): return bytes.fromhex("08B90000") + struct.pack(">I", addr)
def vector(target, addr):
    return ml(0x4EF90000 | ((target >> 16) & 0xffff), addr) + mw(target & 0xffff, addr + 4)
def ones_add32(total, value):
    total += value
    return (total & 0xffffffff) + (total >> 32)

def bne_word(c):
    pos = len(c); c += bytes.fromhex("66000000"); return pos

def bra_word(c):
    pos = len(c); c += bytes.fromhex("60000000"); return pos

def patch_word_branch(c, pos, target):
    disp = target - (pos + 4)
    if not -32768 <= disp <= 32767:
        raise ValueError("branch displacement out of range")
    struct.pack_into(">h", c, pos + 2, disp)

def cmp_abs(c, expected, addr):
    c += bytes.fromhex("0CB9") + struct.pack(">II", expected, addr)
    return bne_word(c)

def cmp_d0(c, expected):
    c += bytes.fromhex("0C80") + struct.pack(">I", expected)
    return bne_word(c)


def build():
    image = bytearray([0xff]) * ROM_SIZE
    struct.pack_into(">II", image, 0, INITIAL_SP, RESET_PC)

    c = bytearray()
    c += bytes.fromhex("46FC2700")
    c += mb(0x03, CIAA_DDRA)
    c += bclr0(CIAA_PRA)
    c += ml(EXEC_BASE, 4)

    c += ml(0, EXEC_BASE + 0)
    c += ml(0, EXEC_BASE + 4)
    c += mw(0x0900, EXEC_BASE + 8)
    c += ml(IDSTRING_ADDR, EXEC_BASE + 10)
    c += mw(0, EXEC_BASE + 14)
    c += mw(264, EXEC_BASE + 16)
    c += mw(34, EXEC_BASE + 18)
    c += mw(40, EXEC_BASE + 20)
    c += mw(4, EXEC_BASE + 22)
    c += ml(IDSTRING_ADDR, EXEC_BASE + 24)
    c += ml(0, EXEC_BASE + 28)
    c += mw(0, EXEC_BASE + 32)

    for offset, target in (
        (234, INSERT_FUNC), (240, ADDHEAD_FUNC), (246, ADDTAIL_FUNC),
        (252, REMOVE_FUNC), (258, REMHEAD_FUNC), (264, REMTAIL_FUNC),
    ):
        c += vector(target, EXEC_BASE - offset)

    c += ml(LIST_ADDR + 4, LIST_ADDR + 0)
    c += ml(0, LIST_ADDR + 4)
    c += ml(LIST_ADDR + 0, LIST_ADDR + 8)
    c += mw(0, LIST_ADDR + 12)
    for node in (NODE1, NODE2, NODE3):
        c += ml(0, node + 0)
        c += ml(0, node + 4)

    # Checkpoint colours identify the next call that fails to return.
    c += mw(0x0f00, COLOR00)
    c += b"\x4d\xf9" + struct.pack(">I", EXEC_BASE)

    c += b"\x41\xf9" + struct.pack(">I", LIST_ADDR)
    c += b"\x43\xf9" + struct.pack(">I", NODE1)
    c += bytes.fromhex("4EAEFF0A")

    c += mw(0x0ff0, COLOR00)
    c += b"\x41\xf9" + struct.pack(">I", LIST_ADDR)
    c += b"\x43\xf9" + struct.pack(">I", NODE2)
    c += bytes.fromhex("4EAEFF0A")

    c += mw(0x00ff, COLOR00)
    c += b"\x41\xf9" + struct.pack(">I", LIST_ADDR)
    c += b"\x43\xf9" + struct.pack(">I", NODE3)
    c += b"\x45\xf9" + struct.pack(">I", NODE1)
    c += bytes.fromhex("4EAEFF16")

    failures = []
    failures += [cmp_abs(c, NODE1, LIST_ADDR + 0)]
    failures += [cmp_abs(c, NODE2, LIST_ADDR + 8)]
    failures += [cmp_abs(c, NODE3, NODE1 + 0)]
    failures += [cmp_abs(c, NODE1, NODE3 + 4)]
    failures += [cmp_abs(c, NODE2, NODE3 + 0)]
    failures += [cmp_abs(c, NODE3, NODE2 + 4)]

    c += mw(0x0f0f, COLOR00)
    c += b"\x43\xf9" + struct.pack(">I", NODE3)
    c += bytes.fromhex("4EAEFF04")
    failures += [cmp_abs(c, NODE2, NODE1 + 0)]
    failures += [cmp_abs(c, NODE1, NODE2 + 4)]

    c += mw(0x0fff, COLOR00)
    c += b"\x41\xf9" + struct.pack(">I", LIST_ADDR)
    c += bytes.fromhex("4EAEFEF8")
    failures += [cmp_d0(c, NODE2)]
    failures += [cmp_abs(c, NODE1, LIST_ADDR + 8)]
    failures += [cmp_abs(c, LIST_ADDR + 4, NODE1 + 0)]

    c += mw(0x0f80, COLOR00)
    c += b"\x41\xf9" + struct.pack(">I", LIST_ADDR)
    c += bytes.fromhex("4EAEFEF8")
    failures += [cmp_d0(c, NODE1)]
    failures += [cmp_abs(c, LIST_ADDR + 4, LIST_ADDR + 0)]
    failures += [cmp_abs(c, LIST_ADDR + 0, LIST_ADDR + 8)]

    c += mw(0x080f, COLOR00)
    c += b"\x41\xf9" + struct.pack(">I", LIST_ADDR)
    c += bytes.fromhex("4EAEFEF8")
    c += bytes.fromhex("4A80")
    failures += [bne_word(c)]

    c += mw(0x0888, COLOR00)
    c += b"\x41\xf9" + struct.pack(">I", LIST_ADDR)
    c += b"\x43\xf9" + struct.pack(">I", NODE3)
    c += bytes.fromhex("247C00000000")
    c += bytes.fromhex("4EAEFF16")
    failures += [cmp_abs(c, NODE3, LIST_ADDR + 0)]
    failures += [cmp_abs(c, LIST_ADDR + 4, NODE3 + 0)]
    failures += [cmp_abs(c, LIST_ADDR, NODE3 + 4)]

    c += mw(0x008f, COLOR00)
    c += b"\x41\xf9" + struct.pack(">I", LIST_ADDR)
    c += bytes.fromhex("4EAEFEFE")
    failures += [cmp_d0(c, NODE3)]
    c += b"\x41\xf9" + struct.pack(">I", LIST_ADDR)
    c += bytes.fromhex("4EAEFEFE")
    c += bytes.fromhex("4A80")
    failures += [bne_word(c)]

    c += mw(0x00f0, COLOR00)
    done_branch = bra_word(c)
    fail = len(c)
    c += mw(0x000f, COLOR00)
    idle = len(c)
    c += bytes.fromhex("60FE")

    for pos in failures:
        patch_word_branch(c, pos, fail)
    patch_word_branch(c, done_branch, idle)
    if 8 + len(c) > 0x0800:
        raise ValueError("bootstrap overlaps routine area")
    image[8:8 + len(c)] = c

    marker = b"LIBREKICK-M2.4\0EXEC-BASIC-LIST-API\0"
    ident = b"exec.library\0LibreKick M2.4 basic list API 40.4\0"
    image[MARKER_OFF:MARKER_OFF + len(marker)] = marker
    image[IDENT_OFF:IDENT_OFF + len(ident)] = ident

    # Insert(A0=list,A1=node,A2=pred). D0 is saved first, so use it as
    # scratch for the NULL-predecessor test. TST.L A2 is illegal on 68000.
    insert = bytes.fromhex(
        "2F002F082F092F0A"
        "200A"
        "4A80"
        "6712"
        "2012"
        "2280"
        "234A0004"
        "2040"
        "21490004"
        "2489"
        "6010"
        "2010"
        "2280"
        "23480004"
        "2440"
        "25490004"
        "2089"
        "245F225F205F201F4E75"
    )
    addhead = bytes.fromhex(
        "2F002F082F092010228023480004204021490004206F00042089225F205F201F4E75"
    )
    addtail = bytes.fromhex(
        "2F002F082F09"
        "20280008"
        "41E80004"
        "2288"
        "23400004"
        "2040"
        "2089"
        "206F0004"
        "21490008"
        "225F205F201F4E75"
    )
    remove = bytes.fromhex(
        "2F002F012F082F09"
        "20290004"
        "2211"
        "2040"
        "2081"
        "2041"
        "21400004"
        "225F205F221F201F4E75"
    )
    remhead = bytes.fromhex(
        "2F012F082F09201022402211670A208122412348000460027000225F205F221F4E75"
    )
    remtail = bytes.fromhex(
        "2F012F082F09"
        "20280008"
        "2240"
        "22290004"
        "670E"
        "21410008"
        "2241"
        "41E80004"
        "2288"
        "6002"
        "7000"
        "225F205F221F4E75"
    )

    routines = [
        (0x0800, insert), (0x0840, addhead), (0x0880, addtail),
        (0x08C0, remove), (0x0900, remhead), (0x0940, remtail),
    ]
    for (off, code), (next_off, _) in zip(routines, routines[1:] + [(MARKER_OFF, b"")]):
        if off + len(code) > next_off:
            raise ValueError(f"routine at 0x{off:x} overlaps next region")
        image[off:off + len(code)] = code

    struct.pack_into(">I", image, ROM_SIZE - 4, 0)
    total = 0
    for off in range(0, ROM_SIZE - 4, 4):
        total = ones_add32(total, struct.unpack_from(">I", image, off)[0])
    total = (total & 0xffffffff) + (total >> 32)
    struct.pack_into(">I", image, ROM_SIZE - 4, (~total) & 0xffffffff)
    return image

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: make_m2_4_rom.py OUTPUT")
    out = Path(sys.argv[1]); data = build(); out.write_bytes(data)
    print(f"M2.4b ROM built: {out} ({len(data)} bytes)")
