#!/usr/bin/env python3
"""Build LibreKick M2.27: qualify bidirectional dynamic FreeMem coalescing."""
from pathlib import Path
import struct, sys
import make_m2_26_rom as p
import make_m2_17_rom as m

MARKER=b'LIBREKICK-M2.27\0EXEC-DYNAMIC-BIDIRECTIONAL-MERGE\0'
IDENT=b'exec.library\0LibreKick M2.27 dynamic bidirectional FreeMem merge slice 40.27\0'
PROBE_OFF=0x2A00
PROBE_END=0x2C00


def build():
    image=bytearray(p.build())

    # Chain after M2.26. This slice isolates the case where one FreeMem call
    # must coalesce with both an already-free predecessor and successor.
    prev=image[p.PROBE_OFF:p.PROBE_END]
    sig=bytes.fromhex('33FC00F000DFF1806000')
    gp=prev.rfind(sig)
    if gp<0: raise ValueError('M2.26 final success gate not found')
    good_abs=p.PROBE_OFF+gp; branch_pos=good_abs+8
    test_abs=PROBE_OFF

    c=bytearray(); fails=[]
    def alloc(size,flags,expect):
        c.extend(bytes.fromhex('203C')+struct.pack('>I',size)+bytes.fromhex('223C')+struct.pack('>I',flags)+bytes.fromhex('4EAEFF3A'))
        fails.append(m.cmpd0(c,expect))
    def free(addr,size):
        c.extend(bytes.fromhex('227C')+struct.pack('>I',addr)+bytes.fromhex('203C')+struct.pack('>I',size)+bytes.fromhex('4EAEFF2E'))
    def avail(flags,expect):
        c.extend(bytes.fromhex('223C')+struct.pack('>I',flags)+bytes.fromhex('4EAEFF28'))
        fails.append(m.cmpd0(c,expect))

    alloc(m.FAST_SIZE,m.MEMF_FAST,m.FAST_BASE)
    alloc(0x100,m.MEMF_FAST,m.APAY)
    alloc(0x100,m.MEMF_FAST,m.APAY+0x100)
    alloc(0x100,m.MEMF_FAST,m.APAY+0x200)

    # Free A0 first. Then free A2, which merges with the existing tail.
    # Free list becomes:
    #   $9020/$100 -> $9220/$DE0
    # while A1 at $9120 remains allocated between them.
    free(m.APAY,0x100)
    free(m.APAY+0x200,0x100)
    right=m.APAY+0x200
    right_bytes=m.AFREE-0x200
    fails += [
        m.cmpabs(c,m.APAY,m.ABASE+m.MH_FIRST),
        m.cmpabs(c,right,m.APAY),
        m.cmpabs(c,0x100,m.APAY+4),
        m.cmpabs(c,0,right),
        m.cmpabs(c,right_bytes,right+4),
        m.cmpabs(c,m.AFREE-0x100,m.ABASE+m.MH_FREE),
    ]

    # Free A1. It is exactly adjacent to both free neighbors. The FreeMem core
    # must first fold in the successor and then fold the result into the
    # predecessor, leaving one complete A chunk.
    free(m.APAY+0x100,0x100)
    fails += [
        m.cmpabs(c,m.APAY,m.ABASE+m.MH_FIRST),
        m.cmpabs(c,0,m.APAY),
        m.cmpabs(c,m.AFREE,m.APAY+4),
        m.cmpabs(c,m.AFREE,m.ABASE+m.MH_FREE),
    ]

    free(m.FAST_BASE,m.FAST_SIZE)
    avail(m.MEMF_FAST,m.FAST_SIZE+m.AFREE+m.CFREE)

    c+=m.mw(0x00f0,m.COLOR00); ok=m.branch(c,0x6000)
    bad=len(c); c+=m.mw(0x000f,m.COLOR00)
    idle=len(c); c+=bytes.fromhex('60FE')
    for fail in fails: m.patch(c,fail,bad)
    m.patch(c,ok,idle)
    if test_abs+len(c)>PROBE_END: raise ValueError('M2.27 runtime probe exceeds dedicated ROM window')
    if any(b != 0xff for b in image[test_abs:test_abs+len(c)]):
        raise ValueError('M2.27 runtime probe window is not unused')
    image[test_abs:test_abs+len(c)]=c
    struct.pack_into('>h',image,branch_pos+2,test_abs-(branch_pos+2))

    image[m.MARKER_OFF:m.IDENT_OFF]=b'\xff'*(m.IDENT_OFF-m.MARKER_OFF)
    image[m.MARKER_OFF:m.MARKER_OFF+len(MARKER)]=MARKER
    image[m.IDENT_OFF:m.NAME_A_OFF]=b'\xff'*(m.NAME_A_OFF-m.IDENT_OFF)
    image[m.IDENT_OFF:m.IDENT_OFF+len(IDENT)]=IDENT

    struct.pack_into('>I',image,m.ROM_SIZE-4,0); total=0
    for off in range(0,m.ROM_SIZE-4,4): total=m.ones(total,struct.unpack_from('>I',image,off)[0])
    total=(total&0xffffffff)+(total>>32)
    struct.pack_into('>I',image,m.ROM_SIZE-4,(~total)&0xffffffff)
    return image

if __name__=='__main__':
    if len(sys.argv)!=2: raise SystemExit('usage: make_m2_27_rom.py OUTPUT')
    out=Path(sys.argv[1]); data=build(); out.write_bytes(data)
    print(f'M2.27 ROM built: {out} ({len(data)} bytes)')
