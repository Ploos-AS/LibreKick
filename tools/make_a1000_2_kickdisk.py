#!/usr/bin/env python3
"""Build deterministic LibreKick A1000.6 WCS shared-Exec payload/disk."""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import struct
import sys
from librekick_exec_abi import EXEC_BASE, LIB_VERSION_OFF, LIB_REVISION_OFF, LIB_IDSTRING_OFF, EXEC_VERSION
from librekick_exec_runtime import SYSBASE_ADDR, get_sysbase_code, jsr_absolute

SECTOR_SIZE = 512
ADF_SIZE = 80 * 2 * 11 * SECTOR_SIZE
WCS_SIZE = 256 * 1024
WCS_BASE = 0x00FC0000
RESET_SP = 0x0007FFFC
ENTRY_PC = WCS_BASE + 8
PAYLOAD_OFFSET = SECTOR_SIZE
MAGIC = b"LIBREKICK-A1000\0"
FORMAT_VERSION = 2
PAYLOAD_MARKER = b"LIBREKICK-A1000.6\0WCS-SHARED-EXEC-RUNTIME\0"
DISK_MARKER = b"LIBREKICK-A1000.6\0KICKDISK-CONTAINER\0"
IDENT = b"exec.library\0LibreKick A1000.6 shared Exec runtime 40.6\0"
IDENT_OFF = 0x180
GETSYSBASE_OFF = 0x200
COLOR00 = 0x00DFF180
REVISION = 6


def _ml(value: int, addr: int) -> bytes:
    return bytes.fromhex("23fc") + struct.pack(">II", value, addr)


def _mw(value: int, addr: int) -> bytes:
    return bytes.fromhex("33fc") + struct.pack(">H", value) + struct.pack(">I", addr)


def _cmp_l(value: int, addr: int) -> bytes:
    return bytes.fromhex("0cb9") + struct.pack(">II", value, addr)


def _cmp_w(value: int, addr: int) -> bytes:
    return bytes.fromhex("0c79") + struct.pack(">H", value) + struct.pack(">I", addr)


def _cmp_d0_l(value: int) -> bytes:
    return bytes.fromhex("0c80") + struct.pack(">I", value)


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
    """Install Exec ABI state, call shared GetSysBase, and self-check it."""
    code = bytearray()
    ident_addr = WCS_BASE + IDENT_OFF
    primitive_addr = WCS_BASE + GETSYSBASE_OFF
    code += _ml(EXEC_BASE, SYSBASE_ADDR)
    code += _mw(EXEC_VERSION, EXEC_BASE + LIB_VERSION_OFF)
    code += _mw(REVISION, EXEC_BASE + LIB_REVISION_OFF)
    code += _ml(ident_addr, EXEC_BASE + LIB_IDSTRING_OFF)
    failures = []
    code += _cmp_l(EXEC_BASE, SYSBASE_ADDR); failures.append(_branch(code, 0x6600))
    code += _cmp_w(EXEC_VERSION, EXEC_BASE + LIB_VERSION_OFF); failures.append(_branch(code, 0x6600))
    code += _cmp_w(REVISION, EXEC_BASE + LIB_REVISION_OFF); failures.append(_branch(code, 0x6600))
    code += _cmp_l(ident_addr, EXEC_BASE + LIB_IDSTRING_OFF); failures.append(_branch(code, 0x6600))
    code += jsr_absolute(primitive_addr)
    code += _cmp_d0_l(EXEC_BASE); failures.append(_branch(code, 0x6600))
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
    primitive = get_sysbase_code()
    if 8 + len(code) > 0x100:
        raise ValueError("A1000.6 runtime overlaps payload marker")
    if GETSYSBASE_OFF + len(primitive) > WCS_SIZE:
        raise ValueError("A1000.6 shared primitive exceeds WCS")
    payload[8:8 + len(code)] = code
    payload[0x100:0x100 + len(PAYLOAD_MARKER)] = PAYLOAD_MARKER
    payload[IDENT_OFF:IDENT_OFF + len(IDENT)] = IDENT
    payload[GETSYSBASE_OFF:GETSYSBASE_OFF + len(primitive)] = primitive
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
    payload_path = out_dir / "librekick-a1000.6-wcs.bin"
    disk_path = out_dir / "librekick-a1000.6-kickdisk.adf"
    payload = build_payload()
    disk = build_disk(payload)
    payload_path.write_bytes(payload)
    disk_path.write_bytes(disk)
    print(f"A1000.6 WCS payload built: {payload_path} ({len(payload)} bytes)")
    print(f"A1000.6 kickdisk built: {disk_path} ({len(disk)} bytes)")
    print(f"exec_base=${EXEC_BASE:08x} version={EXEC_VERSION}.{REVISION} shared_primitive=GetSysBase")
    print(f"wcs_base=${WCS_BASE:08x} entry_pc=${ENTRY_PC:08x} payload_sha256={sha256(payload).hexdigest()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
