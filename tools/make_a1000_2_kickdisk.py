#!/usr/bin/env python3
"""Build the deterministic LibreKick A1000.5 WCS Exec-convergence payload/disk."""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import struct
import sys
from librekick_exec_abi import EXEC_BASE, LIB_VERSION_OFF, LIB_REVISION_OFF, LIB_IDSTRING_OFF, EXEC_VERSION

SECTOR_SIZE = 512
ADF_SIZE = 80 * 2 * 11 * SECTOR_SIZE
WCS_SIZE = 256 * 1024
WCS_BASE = 0x00FC0000
RESET_SP = 0x0007FFFC
ENTRY_PC = WCS_BASE + 8
PAYLOAD_OFFSET = SECTOR_SIZE
MAGIC = b"LIBREKICK-A1000\0"
FORMAT_VERSION = 2
PAYLOAD_MARKER = b"LIBREKICK-A1000.5\0WCS-EXEC-ABI\0"
DISK_MARKER = b"LIBREKICK-A1000.5\0KICKDISK-CONTAINER\0"
IDENT = b"exec.library\0LibreKick A1000.5 WCS Exec ABI convergence 40.5\0"
IDENT_OFF = 0x180
COLOR00 = 0x00DFF180
REVISION = 5


def _ml(value: int, addr: int) -> bytes:
    return bytes.fromhex("23fc") + struct.pack(">II", value, addr)


def _mw(value: int, addr: int) -> bytes:
    return bytes.fromhex("33fc") + struct.pack(">H", value) + struct.pack(">I", addr)


def _cmp_l(value: int, addr: int) -> bytes:
    return bytes.fromhex("0cb9") + struct.pack(">II", value, addr)


def _cmp_w(value: int, addr: int) -> bytes:
    return bytes.fromhex("0c79") + struct.pack(">H", value) + struct.pack(">I", addr)


def _branch(code: bytearray, opcode: int) -> int:
    pos = len(code)
    code += struct.pack(">HH", opcode, 0)
    return pos


def _patch(code: bytearray, pos: int, target: int) -> None:
    disp = target - (pos + 2)
    if not -32768 <= disp <= 32767:
        raise ValueError("branch displacement")
    struct.pack_into(">h", code, pos + 2, disp)


def runtime_code() -> bytes:
    """Install and self-check the first shared Exec ABI state on A1000."""
    code = bytearray()
    ident_addr = WCS_BASE + IDENT_OFF
    code += _ml(EXEC_BASE, 4)
    code += _mw(EXEC_VERSION, EXEC_BASE + LIB_VERSION_OFF)
    code += _mw(REVISION, EXEC_BASE + LIB_REVISION_OFF)
    code += _ml(ident_addr, EXEC_BASE + LIB_IDSTRING_OFF)
    failures = []
    code += _cmp_l(EXEC_BASE, 4); failures.append(_branch(code, 0x6600))
    code += _cmp_w(EXEC_VERSION, EXEC_BASE + LIB_VERSION_OFF); failures.append(_branch(code, 0x6600))
    code += _cmp_w(REVISION, EXEC_BASE + LIB_REVISION_OFF); failures.append(_branch(code, 0x6600))
    code += _cmp_l(ident_addr, EXEC_BASE + LIB_IDSTRING_OFF); failures.append(_branch(code, 0x6600))
    code += _mw(0x00F0, COLOR00)
    good = _branch(code, 0x6000)
    bad = len(code)
    code += _mw(0x000F, COLOR00)
    idle = len(code)
    code += bytes.fromhex("60fe")
    for pos in failures:
        _patch(code, pos, bad)
    _patch(code, good, idle)
    return bytes(code)


def build_payload() -> bytes:
    payload = bytearray(WCS_SIZE)
    struct.pack_into(">II", payload, 0, RESET_SP, ENTRY_PC)
    code = runtime_code()
    payload[8:8 + len(code)] = code
    payload[0x100:0x100 + len(PAYLOAD_MARKER)] = PAYLOAD_MARKER
    payload[IDENT_OFF:IDENT_OFF + len(IDENT)] = IDENT
    return bytes(payload)


def build_disk(payload: bytes) -> bytes:
    image = bytearray(ADF_SIZE)
    digest = sha256(payload).digest()
    image[0:len(MAGIC)] = MAGIC
    struct.pack_into(">IIIIII", image, 16, FORMAT_VERSION, PAYLOAD_OFFSET,
                     len(payload), WCS_BASE, ENTRY_PC, RESET_SP)
    image[40:72] = digest
    image[80:80 + len(DISK_MARKER)] = DISK_MARKER
    image[PAYLOAD_OFFSET:PAYLOAD_OFFSET + len(payload)] = payload
    return bytes(image)


def main() -> int:
    out_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "build/a1000")
    out_dir.mkdir(parents=True, exist_ok=True)
    payload_path = out_dir / "librekick-a1000.5-wcs.bin"
    disk_path = out_dir / "librekick-a1000.5-kickdisk.adf"
    payload = build_payload()
    disk = build_disk(payload)
    payload_path.write_bytes(payload)
    disk_path.write_bytes(disk)
    print(f"A1000.5 WCS payload built: {payload_path} ({len(payload)} bytes)")
    print(f"A1000.5 kickdisk built: {disk_path} ({len(disk)} bytes)")
    print(f"exec_base=${EXEC_BASE:08x} version={EXEC_VERSION}.{REVISION}")
    print(f"wcs_base=${WCS_BASE:08x} entry_pc=${ENTRY_PC:08x} payload_sha256={sha256(payload).hexdigest()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
