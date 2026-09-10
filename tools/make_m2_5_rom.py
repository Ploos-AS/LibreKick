#!/usr/bin/env python3
"""Build LibreKick M2.5: complete classic Exec list/queue slice."""
from pathlib import Path
import struct, sys

ROM_SIZE = 512 * 1024
ROM_BASE = 0x00F80000
INITIAL_SP = 0x0007FFFC
RESET_PC = ROM_BASE + 8
EXEC_BASE = 0x00002C00
COLOR00 = 0x00DFF180
CIAA_PRA = 0x00BFE001
CIAA_DDRA = 0x00BFE201
LIST_ADDR = 0x00001100
NODE1 = 0x00001120
NODE2 = 0x00001140
NODE3 = 0x00001160

MARKER_OFF = 0x1200
IDENT_OFF = 0x1280
ALPHA_OFF = 0x1400
BETA_OFF = 0x1410
MISSING_OFF = 0x1420
IDSTRING_ADDR = ROM_BASE + IDENT_OFF
ALPHA_ADDR = ROM_BASE + ALPHA_OFF
BETA_ADDR = ROM_BASE + BETA_OFF
MISSING_ADDR = ROM_BASE + MISSING_OFF

FUNCS = {
    234: ROM_BASE + 0x0800,
    240: ROM_BASE + 0x0840,
    246: ROM_BASE + 0x0880,
    252: ROM_BASE + 0x08C0,
    258: ROM_BASE + 0x0900,
    264: ROM_BASE + 0x0940,
    270: ROM_BASE + 0x0A00,
    276: ROM_BASE + 0x0A80,
}


def ml(value, addr): return b"\x23\xfc" + struct.pack(">II", value, addr)
def mw(value, addr): return b"\x33\xfc" + struct.pack(">H", value) + struct.pack(">I", addr)
def mb(value, addr): return b"\x13\xfc" + struct.pack(">H", value & 0xff) + struct.pack(">I", addr)
def bclr0(addr): return bytes.fromhex("08B90000") + struct.pack(">I", addr)
def vector(target, addr):
    return ml(0x4EF90000 | ((target >> 16) & 0xffff), addr) + mw(target & 0xffff, addr + 4)
def ones_add32(total, value):
    total += value
    return (total & 0xffffffff) + (total >> 32)

def branch(code, opcode):
    pos = len(code); code += struct.pack(">HH", opcode, 0); return pos

def patch_branch(code, pos, target):
    disp = target - (pos + 4)
    if not -32768 <= disp <= 32767:
        raise ValueError("branch displacement out of range")
    struct.pack_into(">h", code, pos + 2, disp)

def cmp_abs(code, expected, addr):
    code += bytes.fromhex("0CB9") + struct.pack(">II", expected, addr)
    return branch(code, 0x6600)

def cmp_d0(code, expected):
    code += bytes.fromhex("0C80") + struct.pack(">I", expected)
    return branch(code, 0x6600)


def enqueue_code():
    q = bytearray()
    q += bytes.fromhex("2F002F012F082F092F0A2F0B")
    q += bytes.fromhex("7200122900094881")
    q += bytes.fromhex("267C00000000")
    q += bytes.fromhex("2450")
    loop = len(q)
    q += bytes.fromhex("4A92")
    at_insert_1 = branch(q, 0x6700)
    q += bytes.fromhex("7000102A00094880")
    q += bytes.fromhex("B041")
    at_insert_2 = branch(q, 0x6D00)
    q += bytes.fromhex("264A2452")
    again = branch(q, 0x6000)
    insert = len(q)
    q += bytes.fromhex("244B")
    q += bytes.fromhex("4EAEFF16")
    q += bytes.fromhex("265F245F225F205F221F201F4E75")
    patch_branch(q, at_insert_1, insert)
    patch_branch(q, at_insert_2, insert)
    patch_branch(q, again, loop)
    return bytes(q)


def findname_code():
    q = bytearray()
    q += bytes.fromhex("2F082F092F0A2F0B")
    q += bytes.fromhex("2450")
    loop = len(q)
    q += bytes.fromhex("4A92")
    notfound_1 = branch(q, 0x6700)
    q += bytes.fromhex("206A000A")
    q += bytes.fromhex("20084A80")
    next_1 = branch(q, 0x6700)
    q += bytes.fromhex("2649")
    chars = len(q)
    q += bytes.fromhex("1018B01B")
    next_2 = branch(q, 0x6600)
    q += bytes.fromhex("4A00")
    more = branch(q, 0x6600)
    q += bytes.fromhex("200A")
    done_branch = branch(q, 0x6000)
    nxt = len(q)
    q += bytes.fromhex("2452")
    loop_branch = branch(q, 0x6000)
    notfound = len(q)
    q += bytes.fromhex("7000")
    done = len(q)
    q += bytes.fromhex("265F245F225F205F4A804E75")
    patch_branch(q, notfound_1, notfound)
    patch_branch(q, next_1, nxt)
    patch_branch(q, next_2, nxt)
    patch_branch(q, more, chars)
    patch_branch(q, done_branch, done)
    patch_branch(q, loop_branch, loop)
    return bytes(q)


def build():
    image = bytearray([0xff]) * ROM_SIZE
    struct.pack_into(">II", image, 0, INITIAL_SP, RESET_PC)

    c = bytearray()
    c += bytes.fromhex("46FC2700")
    c += mb(0x03, CIAA_DDRA)
    c += bclr0(CIAA_PRA)
    c += ml(EXEC_BASE, 4)

    c += ml(0, EXEC_BASE + 0); c += ml(0, EXEC_BASE + 4)
    c += mw(0x0900, EXEC_BASE + 8); c += ml(IDSTRING_ADDR, EXEC_BASE + 10)
    c += mw(0, EXEC_BASE + 14); c += mw(276, EXEC_BASE + 16)
    c += mw(34, EXEC_BASE + 18); c += mw(40, EXEC_BASE + 20)
    c += mw(5, EXEC_BASE + 22); c += ml(IDSTRING_ADDR, EXEC_BASE + 24)
    c += ml(0, EXEC_BASE + 28); c += mw(0, EXEC_BASE + 32)

    for offset, target in FUNCS.items(): c += vector(target, EXEC_BASE - offset)

    c += ml(LIST_ADDR + 4, LIST_ADDR + 0); c += ml(0, LIST_ADDR + 4)
    c += ml(LIST_ADDR + 0, LIST_ADDR + 8); c += mw(0, LIST_ADDR + 12)
    for node in (NODE1, NODE2, NODE3):
        c += ml(0, node + 0); c += ml(0, node + 4)
    c += mb(10, NODE1 + 9); c += ml(ALPHA_ADDR, NODE1 + 10)
    c += mb(5, NODE2 + 9); c += ml(BETA_ADDR, NODE2 + 10)
    c += mb(10, NODE3 + 9); c += ml(ALPHA_ADDR, NODE3 + 10)

    c += mw(0x0f00, COLOR00)  # red: before Enqueue(node1)
    c += b"\x4d\xf9" + struct.pack(">I", EXEC_BASE)

    # Per-call checkpoints make a non-returning Enqueue unambiguous on a 68000.
    checkpoints = ((NODE1, 0x0f80), (NODE2, 0x0ff0), (NODE3, 0x08f0))
    for node, colour in checkpoints:
        c += b"\x41\xf9" + struct.pack(">I", LIST_ADDR)
        c += b"\x43\xf9" + struct.pack(">I", node)
        c += bytes.fromhex("4EAEFEF2")
        c += mw(colour, COLOR00)

    failures = []
    failures += [cmp_abs(c, NODE1, LIST_ADDR + 0)]
    failures += [cmp_abs(c, NODE2, LIST_ADDR + 8)]
    failures += [cmp_abs(c, NODE3, NODE1 + 0)]
    failures += [cmp_abs(c, NODE1, NODE3 + 4)]
    failures += [cmp_abs(c, NODE2, NODE3 + 0)]
    failures += [cmp_abs(c, NODE3, NODE2 + 4)]

    c += mw(0x0fff, COLOR00)  # white: Enqueue semantics pass; FindName starts

    def call_find(start, name):
        nonlocal c
        c += b"\x41\xf9" + struct.pack(">I", start)
        c += b"\x43\xf9" + struct.pack(">I", name)
        c += bytes.fromhex("4EAEFEEC")

    call_find(LIST_ADDR, ALPHA_ADDR); failures += [cmp_d0(c, NODE1)]
    call_find(NODE1, ALPHA_ADDR); failures += [cmp_d0(c, NODE3)]
    call_find(NODE3, ALPHA_ADDR); c += bytes.fromhex("4A80"); failures += [branch(c, 0x6600)]
    call_find(LIST_ADDR, BETA_ADDR); failures += [cmp_d0(c, NODE2)]
    call_find(LIST_ADDR, MISSING_ADDR); c += bytes.fromhex("4A80"); failures += [branch(c, 0x6600)]

    c += mw(0x00f0, COLOR00)
    done_branch = branch(c, 0x6000)
    fail = len(c); c += mw(0x000f, COLOR00)
    idle = len(c); c += bytes.fromhex("60FE")
    for pos in failures: patch_branch(c, pos, fail)
    patch_branch(c, done_branch, idle)
    if 8 + len(c) > 0x0800: raise ValueError("bootstrap overlaps routine area")
    image[8:8 + len(c)] = c

    routines = {
        0x0800: bytes.fromhex("2F002F082F092F0A200A4A80671220122280234A00042040214900042489601020102280234800042440254900042089245F225F205F201F4E75"),
        0x0840: bytes.fromhex("2F002F082F092010228023480004204021490004206F00042089225F205F201F4E75"),
        0x0880: bytes.fromhex("2F002F082F092028000841E8000422882340000420402089206F000421490008225F205F201F4E75"),
        0x08C0: bytes.fromhex("2F002F012F082F0920290004221120402081204121400004225F205F221F201F4E75"),
        0x0900: bytes.fromhex("2F012F082F09201022402211670A208122412348000460027000225F205F221F4E75"),
        0x0940: bytes.fromhex("2F012F082F0920280008224022290004670E214100082241224141E80004228860027000225F205F221F4E75"),
        0x0A00: enqueue_code(), 0x0A80: findname_code(),
    }
    ordered = sorted(routines.items())
    for (off, code), (next_off, _) in zip(ordered, ordered[1:] + [(MARKER_OFF, b"")]):
        if off + len(code) > next_off: raise ValueError(f"routine at 0x{off:x} overlaps next region")
        image[off:off + len(code)] = code

    marker = b"LIBREKICK-M2.5\0EXEC-QUEUE-FINDNAME\0"
    ident = b"exec.library\0LibreKick M2.5 complete classic list slice 40.5\0"
    image[MARKER_OFF:MARKER_OFF + len(marker)] = marker
    image[IDENT_OFF:IDENT_OFF + len(ident)] = ident
    image[ALPHA_OFF:ALPHA_OFF+6] = b"alpha\0"; image[BETA_OFF:BETA_OFF+5] = b"beta\0"
    image[MISSING_OFF:MISSING_OFF+8] = b"missing\0"

    struct.pack_into(">I", image, ROM_SIZE - 4, 0)
    total = 0
    for off in range(0, ROM_SIZE - 4, 4): total = ones_add32(total, struct.unpack_from(">I", image, off)[0])
    total = (total & 0xffffffff) + (total >> 32)
    struct.pack_into(">I", image, ROM_SIZE - 4, (~total) & 0xffffffff)
    return image

if __name__ == "__main__":
    if len(sys.argv) != 2: raise SystemExit("usage: make_m2_5_rom.py OUTPUT")
    out = Path(sys.argv[1]); data = build(); out.write_bytes(data)
    print(f"M2.5 ROM built: {out} ({len(data)} bytes)")
