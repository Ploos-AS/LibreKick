#!/usr/bin/env python3
"""Static validation for LibreKick A1000.12 private two-task WCS payload/disk."""
from hashlib import sha256
from pathlib import Path
import struct, sys
from librekick_exec_abi import EXEC_BASE, LIB_VERSION_OFF, LIB_REVISION_OFF, LIB_IDSTRING_OFF, EXEC_VERSION
from librekick_exec_runtime import SYSBASE_ADDR, THIS_TASK_OFF, TC_SPREG_OFF
import make_a1000_12_kickdisk as b


def main():
    root=Path(sys.argv[1] if len(sys.argv)>1 else 'build/a1000')
    pp=root/'librekick-a1000.12-wcs.bin'; dp=root/'librekick-a1000.12-kickdisk.adf'
    payload=pp.read_bytes(); disk=dp.read_bytes()
    assert len(payload)==b.WCS_SIZE and len(disk)==b.ADF_SIZE
    assert disk[:len(b.MAGIC)]==b.MAGIC
    version,offset,length,load_addr,entry_pc,reset_sp=struct.unpack_from('>IIIIII',disk,16)
    assert version==b.FORMAT_VERSION and offset==b.PAYLOAD_OFFSET and length==b.WCS_SIZE
    assert (load_addr,entry_pc,reset_sp)==(b.WCS_BASE,b.ENTRY_PC,b.RESET_SP)
    assert disk[40:72]==sha256(payload).digest()
    assert disk[offset:offset+length]==payload
    assert disk[80:80+len(b.DISK_MARKER)]==b.DISK_MARKER
    assert struct.unpack_from('>II',payload,0)==(b.RESET_SP,b.ENTRY_PC)
    code=b.runtime_code(); sw=b.switch_code(); tb=b.task_b_code()
    assert payload[8:8+len(code)]==code
    assert payload[b.MARKER_OFF:b.MARKER_OFF+len(b.PAYLOAD_MARKER)]==b.PAYLOAD_MARKER
    assert payload[b.IDENT_OFF:b.IDENT_OFF+len(b.IDENT)]==b.IDENT
    assert payload[b.SWITCH_OFF:b.SWITCH_OFF+len(sw)]==sw
    assert payload[b.TASK_B_ENTRY_OFF:b.TASK_B_ENTRY_OFF+len(tb)]==tb
    assert SYSBASE_ADDR==4 and THIS_TASK_OFF==0x114 and TC_SPREG_OFF==0x36 and EXEC_BASE==0x3400
    assert (LIB_VERSION_OFF,LIB_REVISION_OFF,LIB_IDSTRING_OFF)==(20,22,24)
    assert EXEC_VERSION==40 and b.REVISION==12
    assert b.TASK_A!=b.TASK_B and b.D_REGS==list(range(2,8)) and b.A_REGS==list(range(2,7))
    assert bytes.fromhex('40e7') in sw and bytes.fromhex('46df') in sw
    assert struct.pack('>H',TC_SPREG_OFF) in sw and struct.pack('>H',THIS_TASK_OFF) in sw
    assert struct.pack('>I',b.TASK_A) in code and struct.pack('>I',b.TASK_B) in code
    assert struct.pack('>I',b.B_MAGIC) in tb and struct.pack('>I',b.B_MAGIC) in code
    for r in b.D_REGS:
        assert struct.pack('>I',b.A_D[r]) in code
        assert struct.pack('>I',b.B_D[r]) in b.prepared_frame(b.WCS_BASE+b.TASK_B_ENTRY_OFF,b.B_D,b.B_A)
    for r in b.A_REGS:
        assert struct.pack('>I',b.A_A[r]) in code
        assert struct.pack('>I',b.B_A[r]) in b.prepared_frame(b.WCS_BASE+b.TASK_B_ENTRY_OFF,b.B_D,b.B_A)
    assert bytes.fromhex('33fc00f000dff180') in code
    assert bytes.fromhex('33fc0f0000dff180') in code
    print(f'A1000.12 static check PASS: {dp} ({len(disk)} bytes)')
    print(f'WCS payload={len(payload)} bytes load=${load_addr:08x} entry=${entry_pc:08x}')
    print(f'shared_exec=ExecBase@${EXEC_BASE:08x} version={EXEC_VERSION}.{b.REVISION}')
    print('context=SR,D2-D7,A2-A6,tc_SPReg; tasks=A,B')
    print(f'payload_sha256={sha256(payload).hexdigest()}')
    print('scope=private deterministic two-task switch; public Exec scheduler not claimed')
    return 0

if __name__=='__main__': raise SystemExit(main())
