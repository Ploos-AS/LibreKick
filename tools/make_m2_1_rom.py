#!/usr/bin/env python3
"""Build LibreKick M2.1: Library-layout and negative-vector ABI foundation."""
from pathlib import Path
import struct
import sys

ROM_SIZE = 512 * 1024
ROM_BASE = 0x00F80000
INITIAL_SP = 0x0007FFFC
RESET_PC = ROM_BASE + 8
EXEC_BASE = 0x00002100
PROBE_VECTOR = EXEC_BASE - 6
PROBE_FUNC = ROM_BASE + 0x300
PROBE_RESULT_ADDR = 0x00001040
PROBE_MAGIC = 0x4C4B5631  # LKV1
COLOR00 = 0x00DFF180
IDSTRING_ADDR = ROM_BASE + 0x180


def ml_imm_abs(value: int, address: int) -> bytes:
    return b"\x23\xfc" + struct.pack(">II", value, address)


def mw_imm_abs(value: int, address: int) -> bytes:
    return b"\x33\xfc" + struct.pack(">H", value) + struct.pack(">I", address)


def ones_add32(total: int, value: int) -> int:
    total += value
    return (total & 0xFFFFFFFF) + (total >> 32)


def build() -> bytearray:
    image = bytearray([0xFF]) * ROM_SIZE
    struct.pack_into(">II", image, 0, INITIAL_SP, RESET_PC)

    code = bytearray()
    code += bytes.fromhex("46FC2700")  # move.w #$2700,sr
    code += ml_imm_abs(EXEC_BASE, 0x00000004)  # canonical SysBase pointer

    # struct Library-compatible positive region at EXEC_BASE.
    code += ml_imm_abs(0, EXEC_BASE + 0)       # ln_Succ
    code += ml_imm_abs(0, EXEC_BASE + 4)       # ln_Pred
    code += mw_imm_abs(0x0900, EXEC_BASE + 8)  # ln_Type=NT_LIBRARY, ln_Pri=0
    code += ml_imm_abs(IDSTRING_ADDR, EXEC_BASE + 10)  # ln_Name
    code += mw_imm_abs(0, EXEC_BASE + 14)      # lib_Flags/lib_pad
    code += mw_imm_abs(6, EXEC_BASE + 16)      # lib_NegSize
    code += mw_imm_abs(34, EXEC_BASE + 18)     # lib_PosSize
    code += mw_imm_abs(40, EXEC_BASE + 20)     # lib_Version
    code += mw_imm_abs(1, EXEC_BASE + 22)      # lib_Revision
    code += ml_imm_abs(IDSTRING_ADDR, EXEC_BASE + 24)  # lib_IdString
    code += ml_imm_abs(0, EXEC_BASE + 28)      # lib_Sum
    code += mw_imm_abs(0, EXEC_BASE + 32)      # lib_OpenCnt

    # First real negative-vector mechanism: JMP absolute at -6(a6).
    code += ml_imm_abs(0x4EF900F8, PROBE_VECTOR)
    code += mw_imm_abs(PROBE_FUNC & 0xFFFF, PROBE_VECTOR + 4)

    # Call the vector through an A6 library base, exactly as Amiga libraries do.
    code += b"\x4d\xf9" + struct.pack(">I", EXEC_BASE)  # lea EXEC_BASE,a6
    code += bytes.fromhex("4EAEFFFA")                    # jsr -6(a6)
    code += b"\x23\xc0" + struct.pack(">I", PROBE_RESULT_ADDR)  # move.l d0,abs.l
    code += mw_imm_abs(0x0F0F, COLOR00)                   # magenta success marker
    code += bytes.fromhex("60FE")                        # idle loop
    image[8:8 + len(code)] = code

    marker = b"LIBREKICK-M2.1\0LIBRARY-ABI-VECTOR-FOUNDATION\0"
    image[0x100:0x100 + len(marker)] = marker
    ident = b"exec.library\0LibreKick M2.1 ABI foundation 40.1\0"
    image[0x180:0x180 + len(ident)] = ident

    probe = b"\x20\x3c" + struct.pack(">I", PROBE_MAGIC) + b"\x4e\x75"
    image[0x300:0x300 + len(probe)] = probe

    struct.pack_into(">I", image, ROM_SIZE - 4, 0)
    total = 0
    for offset in range(0, ROM_SIZE - 4, 4):
        total = ones_add32(total, struct.unpack_from(">I", image, offset)[0])
    total = (total & 0xFFFFFFFF) + (total >> 32)
    struct.pack_into(">I", image, ROM_SIZE - 4, (~total) & 0xFFFFFFFF)
    return image


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: make_m2_1_rom.py OUTPUT")
    out = Path(sys.argv[1])
    image = build()
    out.write_bytes(image)
    print(f"M2.1 ROM built: {out} ({len(image)} bytes)")


if __name__ == "__main__":
    main()
