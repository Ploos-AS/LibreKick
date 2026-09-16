#!/usr/bin/env python3
"""Static validation for LibreKick M2.47."""
from pathlib import Path
import struct,sys
import make_m2_47_rom as b

def ones(t,v):
    t+=v; return (t&0xffffffff)+(t>>32)

def main():
    p=Path(sys.argv[1] if len(sys.argv)>1 else 'build/librekick-m2_47.rom'); data=p.read_bytes()
    assert len(data)==512*1024
    hand=b.context_handoff_code(); resume=b.context_resume_code(); probe=b.probe_code()
    assert data[b.CONTEXT_HANDOFF_OFF:b.CONTEXT_HANDOFF_OFF+len(hand)]==hand
    assert data[b.CONTEXT_RESUME_OFF:b.CONTEXT_RESUME_OFF+len(resume)]==resume
    assert data[b.PROBE_OFF:b.PROBE_OFF+len(probe)]==probe
    assert b.MARKER in data and b.IDENT in data
    assert b.D_REGS==list(range(2,8)) and b.A_REGS==list(range(2,7))
    assert bytes.fromhex('40f9') in hand and bytes.fromhex('46df') in resume
    assert bytes.fromhex('33fc00f000dff180') in probe and bytes.fromhex('33fc000f00dff180') in probe
    t=0
    for off in range(0,len(data),4): t=ones(t,struct.unpack_from('>I',data,off)[0])
    t=(t&0xffffffff)+(t>>32); assert t==0xffffffff, f'bad checksum {t:08x}'
    print(f'M2.47 check PASS: {p} ({len(data)} bytes)')
    print(f'context_handoff=${b.ROM_BASE+b.CONTEXT_HANDOFF_OFF:08x} context_resume=${b.ROM_BASE+b.CONTEXT_RESUME_OFF:08x} probe=${b.ROM_BASE+b.PROBE_OFF:08x}')
    print('context=SR,D2-D7,A2-A6; checksum=0xffffffff')
    print('scope=private CPU context frame; public Exec scheduler not claimed')
    return 0
if __name__=='__main__': raise SystemExit(main())
