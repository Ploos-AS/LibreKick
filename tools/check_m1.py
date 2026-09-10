#!/usr/bin/env python3
from pathlib import Path
import struct
import sys

ROM_SIZE = 512 * 1024
ROM_BASE = 0x00F80000
EXPECTED_SP = 0x0007FFFC
EXPECTED_PC = ROM_BASE + 8
EXPECTED_CODE = bytes.fromhex(
    "46FC2700"
    "23FC4C4B303100001000"
    "33FC000F00DFF180"
    "60FE"
)
MARKER = b"LIBREKICK-M1\0BOOTSTRAP-68000\0"


def ones_add32(total: int, value: int) -> int:
    total += value
    return (total & 0xFFFFFFFF) + (total >> 32)


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: check_m1.py ROM")
    p = Path(sys.argv[1])
    data = p.read_bytes()
    assert len(data) == ROM_SIZE, f"wrong ROM size: {len(data)}"

    sp, pc = struct.unpack_from(">II", data, 0)
    assert sp == EXPECTED_SP, f"bad initial SP: 0x{sp:08x}"
    assert pc == EXPECTED_PC, f"bad reset PC: 0x{pc:08x}"
    assert data[8:8 + len(EXPECTED_CODE)] == EXPECTED_CODE, "bootstrap opcode mismatch"
    assert data[0x40:0x40 + len(MARKER)] == MARKER, "missing M1 marker"

    total = 0
    for offset in range(0, len(data), 4):
        total = ones_add32(total, struct.unpack_from(">I", data, offset)[0])
    total = (total & 0xFFFFFFFF) + (total >> 32)
    assert total == 0xFFFFFFFF, f"ROM checksum mismatch: 0x{total:08x}"

    print(f"M1 check PASS: {p} ({len(data)} bytes)")
    print(f"reset SP=0x{sp:08x} PC=0x{pc:08x}; checksum=0x{total:08x}")


if __name__ == "__main__":
    main()
