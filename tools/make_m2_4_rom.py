#!/usr/bin/env python3
"""Build LibreKick M2.4: complete basic Exec doubly-linked list primitive slice."""
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

    # struct Library-compatible header; negative space reaches RemTail(-264).
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

    # Public Exec list vectors: Insert/AddHead/AddTail/Remove/RemHead/RemTail.
    for offset, target in (
        (234, INSERT_FUNC), (240, ADDHEAD_FUNC), (246, ADDTAIL_FUNC),
        (252, REMOVE_FUNC), (258, REMHEAD_FUNC), (264, REMTAIL_FUNC),
    ):
        c += vector(target, EXEC_BASE - offset)

    # NewList-equivalent empty List and three probe Nodes.
    c += ml(LIST_ADDR + 4, LIST_ADDR + 0)
    c += ml(0, LIST_ADDR + 4)
    c += ml(LIST_ADDR + 0, LIST_ADDR + 8)
    c += mw(0, LIST_ADDR + 12)
    for node in (NODE1, NODE2, NODE3):
        c += ml(0, node + 0)
        c += ml(0, node + 4)

    c += mw(0x0f00, COLOR00)  # red while semantic probe is running
    c += b"\x4d\xf9" + struct.pack(">I", EXEC_BASE)  # A6=SysBase

    # AddTail(node1), AddTail(node2).
    for node in (NODE1, NODE2):
        c += b"\x41\xf9" + struct.pack(">I", LIST_ADDR)
        c += b"\x43\xf9" + struct.pack(">I", node)
        c += bytes.fromhex("4EAEFF0A")  # -246(a6)

    # Insert node3 after node1 -> [node1,node3,node2].
    c += b"\x41\xf9" + struct.pack(">I", LIST_ADDR)
    c += b"\x43\xf9" + struct.pack(">I", NODE3)
    c += b"\x45\xf9" + struct.pack(">I", NODE1)
    c += bytes.fromhex("4EAEFF16")  # -234(a6)

    failures = []
    failures += [cmp_abs(c, NODE1, LIST_ADDR + 0)]
    failures += [cmp_abs(c, NODE2, LIST_ADDR + 8)]
    failures += [cmp_abs(c, NODE3, NODE1 + 0)]
    failures += [cmp_abs(c, NODE1, NODE3 + 4)]
    failures += [cmp_abs(c, NODE2, NODE3 + 0)]
    failures += [cmp_abs(c, NODE3, NODE2 + 4)]

    # Remove node3 -> [node1,node2].
    c += b"\x43\xf9" + struct.pack(">I", NODE3)
    c += bytes.fromhex("4EAEFF04")  # -252(a6)
    failures += [cmp_abs(c, NODE2, NODE1 + 0)]
    failures += [cmp_abs(c, NODE1, NODE2 + 4)]

    # RemTail -> node2; then node1; then NULL on empty list.
    c += b"\x41\xf9" + struct.pack(">I", LIST_ADDR)
    c += bytes.fromhex("4EAEFEF8")
    failures += [cmp_d0(c, NODE2)]
    failures += [cmp_abs(c, NODE1, LIST_ADDR + 8)]
    failures += [cmp_abs(c, LIST_ADDR + 4, NODE1 + 0)]

    c += b"\x41\xf9" + struct.pack(">I", LIST_ADDR)
    c += bytes.fromhex("4EAEFEF8")
    failures += [cmp_d0(c, NODE1)]
    failures += [cmp_abs(c, LIST_ADDR + 4, LIST_ADDR + 0)]
    failures += [cmp_abs(c, LIST_ADDR + 0, LIST_ADDR + 8)]

    c += b"\x41\xf9" + struct.pack(">I", LIST_ADDR)
    c += bytes.fromhex("4EAEFEF8")
    c += bytes.fromhex("4A80")  # tst.l d0
    failures += [bne_word(c)]

    c += mw(0x00f0, COLOR00)  # green: all semantics passed
    done_branch = bra_word(c)
    fail = len(c)
    c += mw(0x000f, COLOR00)  # blue: a semantic assertion failed
    idle = len(c)
    c += bytes.fromhex("60FE")

    for pos in failures:
        patch_word_branch(c, pos, fail)
    patch_word_branch(c, done_branch, idle)
    image[8:8 + len(c)] = c

    marker = b"LIBREKICK-M2.4\0EXEC-BASIC-LIST-API\0"
    ident = b"exec.library\0LibreKick M2.4 basic list API 40.4\0"
    image[MARKER_OFF:MARKER_OFF + len(marker)] = marker
    image[IDENT_OFF:IDENT_OFF + len(ident)] = ident

    # Insert(A0=list,A1=node,A2=pred), no return. Preserve D0/A0/A1/A2.
    insert = bytes.fromhex(
        "2F002F082F092F0A"      # save d0/a0/a1/a2
        "4A8A"                  # tst.l a2
        "6712"                  # beq.s head
        "2012"                  # d0=pred->succ
        "2280"                  # node->succ=d0
        "234A0004"              # node->pred=pred
        "2040"                  # a0=successor
        "21490004"              # successor->pred=node
        "2489"                  # pred->succ=node
        "600E"                  # bra.s done
        "2010"                  # head: d0=list->head
        "2280"                  # node->succ=d0
        "23480004"              # node->pred=list
        "2440"                  # a2=old head/sentinel
        "25490004"              # old head->pred=node
        "2089"                  # list->head=node
        "245F225F205F201F4E75"  # done: restore a2/a1/a0/d0; rts
    )
    # Qualified M2.3 AddHead/RemHead implementations are retained unchanged.
    addhead = bytes.fromhex(
        "2F002F082F092010228023480004204021490004206F00042089225F205F201F4E75"
    )
    addtail = bytes.fromhex(
        "2F002F082F09"          # save d0/a0/a1
        "20280008"              # d0=list->tailpred
        "41E80004"              # a0=&list->tail
        "2288"                  # node->succ=&tail
        "23400004"              # node->pred=d0
        "2040"                  # a0=old tailpred
        "2089"                  # old tailpred->succ=node
        "206F0004"              # restore list pointer into a0
        "21490008"              # list->tailpred=node
        "225F205F201F4E75"      # restore a1/a0/d0; rts
    )
    remove = bytes.fromhex(
        "2F002F012F082F09"      # save d0/d1/a0/a1
        "20290004"              # d0=node->pred
        "2211"                  # d1=node->succ
        "2040"                  # a0=pred
        "2081"                  # pred->succ=succ
        "2041"                  # a0=succ
        "21400004"              # succ->pred=pred
        "225F205F221F201F4E75"  # restore; rts
    )
    remhead = bytes.fromhex(
        "2F012F082F09201022402211670A208122412348000460027000225F205F221F4E75"
    )
    remtail = bytes.fromhex(
        "2F012F082F09"          # save d1/a0/a1
        "20280008"              # d0=list->tailpred
        "2240"                  # a1=d0
        "22290004"              # d1=node->pred; zero iff empty sentinel
        "670E"                  # beq.s empty
        "21410008"              # list->tailpred=d1
        "2241"                  # a1=pred
        "41E80004"              # a0=&list->tail
        "2288"                  # pred->succ=&tail
        "6002"                  # bra.s done
        "7000"                  # empty: d0=0
        "225F205F221F4E75"      # done: restore a1/a0/d1; rts
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
    print(f"M2.4 ROM built: {out} ({len(data)} bytes)")
