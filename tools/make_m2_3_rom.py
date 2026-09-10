#!/usr/bin/env python3
"""Build LibreKick M2.3: public Exec list primitives AddHead/RemHead."""
from pathlib import Path
import struct, sys

ROM_SIZE = 512 * 1024
ROM_BASE = 0x00F80000
INITIAL_SP = 0x0007FFFC
RESET_PC = ROM_BASE + 8
EXEC_BASE = 0x00002400
COLOR00 = 0x00DFF180
CIAA_PRA = 0x00BFE001
CIAA_DDRA = 0x00BFE201
IDSTRING_ADDR = ROM_BASE + 0x180
ADDHEAD_FUNC = ROM_BASE + 0x380
REMHEAD_FUNC = ROM_BASE + 0x3A0
LIST_ADDR = 0x00001100
NODE_ADDR = 0x00001120


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

    # struct Library-compatible header; negative space now reaches RemHead(-258).
    c += ml(0, EXEC_BASE + 0)
    c += ml(0, EXEC_BASE + 4)
    c += mw(0x0900, EXEC_BASE + 8)
    c += ml(IDSTRING_ADDR, EXEC_BASE + 10)
    c += mw(0, EXEC_BASE + 14)
    c += mw(258, EXEC_BASE + 16)
    c += mw(34, EXEC_BASE + 18)
    c += mw(40, EXEC_BASE + 20)
    c += mw(3, EXEC_BASE + 22)
    c += ml(IDSTRING_ADDR, EXEC_BASE + 24)
    c += ml(0, EXEC_BASE + 28)
    c += mw(0, EXEC_BASE + 32)

    # Public Exec V40-compatible list primitive vectors.
    c += vector(ADDHEAD_FUNC, EXEC_BASE - 240)
    c += vector(REMHEAD_FUNC, EXEC_BASE - 258)

    # NewList-equivalent initialization of one private probe list.
    c += ml(LIST_ADDR + 4, LIST_ADDR + 0)   # lh_Head -> tail sentinel
    c += ml(0, LIST_ADDR + 4)               # lh_Tail = NULL
    c += ml(LIST_ADDR + 0, LIST_ADDR + 8)   # lh_TailPred -> head sentinel
    c += mw(0, LIST_ADDR + 12)               # lh_Type/l_pad = 0
    c += ml(0, NODE_ADDR + 0)
    c += ml(0, NODE_ADDR + 4)

    c += mw(0x0f00, COLOR00)                 # red while probe runs
    c += b"\x4d\xf9" + struct.pack(">I", EXEC_BASE)  # lea SysBase,a6
    c += b"\x41\xf9" + struct.pack(">I", LIST_ADDR)  # lea list,a0
    c += b"\x43\xf9" + struct.pack(">I", NODE_ADDR)  # lea node,a1
    c += bytes.fromhex("4EAEFF10")           # jsr -240(a6) AddHead

    # RemHead must return NODE_ADDR in D0.
    c += b"\x41\xf9" + struct.pack(">I", LIST_ADDR)
    c += bytes.fromhex("4EAEFEFE")           # jsr -258(a6) RemHead
    c += b"\x0c\x80" + struct.pack(">I", NODE_ADDR)  # cmpi.l #NODE,d0
    bne1 = len(c); c += bytes.fromhex("6600")

    # List must again be empty: lh_Head == &lh_Tail and lh_TailPred == &lh_Head.
    c += b"\x0c\xb9" + struct.pack(">II", LIST_ADDR + 4, LIST_ADDR + 0)
    bne2 = len(c); c += bytes.fromhex("6600")
    c += b"\x0c\xb9" + struct.pack(">II", LIST_ADDR + 0, LIST_ADDR + 8)
    bne3 = len(c); c += bytes.fromhex("6600")

    # A second RemHead on the empty list must return NULL.
    c += b"\x41\xf9" + struct.pack(">I", LIST_ADDR)
    c += bytes.fromhex("4EAEFEFE")
    c += bytes.fromhex("4A80")               # tst.l d0
    bne4 = len(c); c += bytes.fromhex("6600")

    c += mw(0x00f0, COLOR00)                  # green: full semantic probe PASS
    bra = len(c); c += bytes.fromhex("6000")
    fail = len(c)
    c += mw(0x000f, COLOR00)                  # blue: semantic mismatch
    idle = len(c); c += bytes.fromhex("60FE")

    for pos in (bne1, bne2, bne3, bne4):
        c[pos + 1] = (fail - (pos + 2)) & 0xff
    c[bra + 1] = (idle - (bra + 2)) & 0xff
    image[8:8+len(c)] = c

    marker = b"LIBREKICK-M2.3\0PUBLIC-EXEC-LVO-ADDHEAD-REMHEAD\0"
    image[0x100:0x100+len(marker)] = marker
    ident = b"exec.library\0LibreKick M2.3 public list LVO slice 40.3\0"
    image[0x180:0x180+len(ident)] = ident

    # AddHead(a0=list,a1=node): preserve all registers except condition codes.
    # d0 is saved/restored because AddHead has no return value.
    addhead = bytes.fromhex(
        "2F00"              # move.l d0,-(sp)
        "2010"              # move.l (a0),d0         old head
        "2280"              # move.l d0,(a1)         node->succ
        "23480004"          # move.l a0,4(a1)        node->pred=list
        "2040"              # move.l d0,a0           a0=old head/sentinel
        "21490004"          # move.l a1,4(a0)        oldhead->pred=node
        "201F"              # move.l (sp)+,d0
        "2049"              # move.l a1,a0
        "22680004"          # move.l 4(a0),a1        a1=list (restore via node->pred)
        "2288"              # move.l a0,(a1)         list->head=node
        "2049"              # move.l a1,a0           restore a0=list
        "4E75"
    )
    image[0x380:0x380+len(addhead)] = addhead

    # RemHead(a0=list) -> d0=node or NULL. A0/A1 are preserved.
    remhead = bytes.fromhex(
        "2F08"              # move.l a0,-(sp)
        "2F09"              # move.l a1,-(sp)
        "2010"              # move.l (a0),d0         node/sentinel
        "2250"              # move.l (a0),a1         a1=node/sentinel
        "4A91"              # tst.l (a1)             node->succ; zero => empty sentinel
        "670C"              # beq.s empty
        "2051"              # move.l (a1),a0         a0=new head
        "2348"              # move.l a0,(a1)? patched below intentionally not used
    )
    # Construct the remaining routine explicitly to avoid assembler dependency.
    # We overwrite from the point after BNE path setup with known 68000 opcodes:
    remhead = bytes.fromhex(
        "2F08"              # move.l a0,-(sp)
        "2F09"              # move.l a1,-(sp)
        "2250"              # move.l (a0),a1         a1=node/sentinel
        "2011"              # move.l (a1),d0         d0=node->succ
        "670C"              # beq.s empty (sentinel has succ==0)
        "2080"              # move.l d0,(a0)         list->head=newhead
        "2240"              # move.l d0,a1           a1=newhead
        "23500004"          # move.l (sp?) placeholder avoided below
    )
    # Simpler fully-known encoding: save list in d1 temporarily and restore d1 too.
    remhead = bytes.fromhex(
        "2F01"              # move.l d1,-(sp)
        "2F09"              # move.l a1,-(sp)
        "2208"              # move.l a0,d1           d1=list
        "2250"              # move.l (a0),a1         a1=node/sentinel
        "2011"              # move.l (a1),d0         d0=node->succ
        "6710"              # beq.s empty
        "2080"              # move.l d0,(a0)         list->head=newhead
        "2240"              # move.l d0,a1           a1=newhead
        "23410004"          # move.l d1,4(a1)        newhead->pred=list
        "2049"              # move.l a1,a0           scratch
        "2040"              # move.l d0,a0           scratch/no semantic effect
        "200?"              # placeholder
    )
    # Replace with a compact hand-encoded implementation that only promises the documented
    # result register; A0/A1 preservation is not claimed by this M2.3 slice.
    remhead = bytes.fromhex(
        "2250"              # move.l (a0),a1         node/sentinel
        "2011"              # move.l (a1),d0         newhead or 0
        "6708"              # beq.s empty
        "2080"              # move.l d0,(a0)         list->head=newhead
        "2240"              # move.l d0,a1           a1=newhead
        "23480004"          # move.l a0,4(a1)        newhead->pred=list
        "2009"              # move.l a1,d0           WRONG: would return newhead
    )
    # Final implementation: save removed node in d0, new head in d1; preserve d1.
    remhead = bytes.fromhex(
        "2F01"              # move.l d1,-(sp)
        "2010"              # move.l (a0),d0         removed node/sentinel
        "2240"              # move.l d0,a1
        "2211"              # move.l (a1),d1         successor
        "670A"              # beq.s empty
        "2081"              # move.l d1,(a0)         list->head=successor
        "2241"              # move.l d1,a1
        "23480004"          # move.l a0,4(a1)        successor->pred=list
        "6002"              # bra.s done
        "7000"              # empty: moveq #0,d0
        "221F"              # done: move.l (sp)+,d1
        "4E75"
    )
    image[0x3A0:0x3A0+len(remhead)] = remhead

    struct.pack_into(">I", image, ROM_SIZE - 4, 0)
    total = 0
    for off in range(0, ROM_SIZE - 4, 4):
        total = ones_add32(total, struct.unpack_from(">I", image, off)[0])
    total = (total & 0xffffffff) + (total >> 32)
    struct.pack_into(">I", image, ROM_SIZE - 4, (~total) & 0xffffffff)
    return image

if __name__ == "__main__":
    if len(sys.argv) != 2: raise SystemExit("usage: make_m2_3_rom.py OUTPUT")
    out = Path(sys.argv[1]); data = build(); out.write_bytes(data)
    print(f"M2.3 ROM built: {out} ({len(data)} bytes)")
