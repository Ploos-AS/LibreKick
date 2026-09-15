#!/usr/bin/env python3
"""Static validation for LibreKick A1000.6 shared-Exec WCS payload/disk."""
from __future__ import annotations
from hashlib import sha256
from pathlib import Path
import struct, sys
from librekick_exec_abi import EXEC_BASE, LIB_VERSION_OFF, LIB_REVISION_OFF, LIB_IDSTRING_OFF, EXEC_VERSION
from librekick_exec_runtime import SYSBASE_ADDR, get_sysbase_code
import make_a1000_2_kickdisk as builder


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "build/a1000")
    payload_path = root / "librekick-a1000.6-wcs.bin"
    disk_path = root / "librekick-a1000.6-kickdisk.adf"
    payload = payload_path.read_bytes(); disk = disk_path.read_bytes()
    assert len(payload) == builder.WCS_SIZE
    assert len(disk) == builder.ADF_SIZE
    assert disk[:len(builder.MAGIC)] == builder.MAGIC
    version, offset, length, load_addr, entry_pc, reset_sp = struct.unpack_from(">IIIIII", disk, 16)
    assert version == builder.FORMAT_VERSION
    assert offset == builder.PAYLOAD_OFFSET and length == builder.WCS_SIZE
    assert load_addr == builder.WCS_BASE and entry_pc == builder.ENTRY_PC and reset_sp == builder.RESET_SP
    assert disk[40:72] == sha256(payload).digest()
    assert disk[80:80 + len(builder.DISK_MARKER)] == builder.DISK_MARKER
    assert disk[offset:offset + length] == payload
    sp, pc = struct.unpack_from(">II", payload, 0)
    assert sp == builder.RESET_SP and pc == builder.ENTRY_PC
    code = builder.runtime_code()
    assert payload[8:8 + len(code)] == code, "A1000.6 shared Exec runtime code mismatch"
    assert payload[0x100:0x100 + len(builder.PAYLOAD_MARKER)] == builder.PAYLOAD_MARKER
    assert payload[builder.IDENT_OFF:builder.IDENT_OFF + len(builder.IDENT)] == builder.IDENT
    primitive = get_sysbase_code()
    assert payload[builder.GETSYSBASE_OFF:builder.GETSYSBASE_OFF + len(primitive)] == primitive
    assert primitive == bytes.fromhex("2039000000044e75"), "shared GetSysBase must remain 68000-safe MOVE.L abs,D0; RTS"
    assert SYSBASE_ADDR == 4
    assert EXEC_BASE == 0x00003400
    assert (LIB_VERSION_OFF, LIB_REVISION_OFF, LIB_IDSTRING_OFF) == (20, 22, 24)
    assert EXEC_VERSION == 40
    print(f"A1000.6 static check PASS: {disk_path} ({len(disk)} bytes)")
    print(f"WCS payload={len(payload)} bytes load=${load_addr:08x} entry=${entry_pc:08x}")
    print(f"shared_exec=ExecBase@${EXEC_BASE:08x} version={EXEC_VERSION}.{builder.REVISION} primitive=GetSysBase")
    print(f"getsysbase_wcs=${builder.WCS_BASE + builder.GETSYSBASE_OFF:08x} bytes={primitive.hex()}")
    print(f"payload_sha256={sha256(payload).hexdigest()}")
    print("format=LibreKick-private bootstrap container v2; full Exec compatibility not claimed")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
