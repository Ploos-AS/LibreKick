#!/usr/bin/env python3
"""Build LibreKick M2.29: qualify 8-byte dynamic AllocMem/FreeMem size alignment."""
from pathlib import Path
import struct, sys
import make_m2_28_rom as p
import make_m2_17_rom as m

MARKER=b'LIBREKICK-M2.29\0EXEC-DYNAMIC-ALLOCATION-ALIGNMENT\0'
IDENT=b'exec.library\0LibreKick M2.29 dynamic allocation alignment slice 40.29\0'
PROBE_OFF=0x2E00
PROBE_END=0x3000


def build():
    image=bytearray(p.build())

    # Chain after M2.28. Isolate the established 8-byte request alignment in
    # the dynamic AllocMem core, then prove that FreeMem applies the same
    # rounding when restoring the chunks.
    prev=image[p.PROBE_OFF:p.PROBE_END]
    sig=bytes.fromhex('33FC00F000DFF1806000')
    gp=prev.rfind(sig)
    if gp<0: raise ValueError('M2.28 final success gate not found')
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

    # Exhaust static FAST and the tiny priority-7 dynamic C region so small
    # alignment probes are forced into dynamic FAST A.
    alloc(m.FAST_SIZE,m.MEMF_FAST,m.FAST_BASE)
    alloc(m.CFREE,m.MEMF_FAST,m.CPAY)

    # Request 1 byte -> 8 bytes consumed. Request 9 bytes -> 16 consumed.
    alloc(1,m.MEMF_FAST,m.APAY)
    alloc(9,m.MEMF_FAST,m.APAY+8)
    fails += [
        m.cmpabs(c,m.APAY+24,m.ABASE+m.MH_FIRST),
        m.cmpabs(c,0,m.APAY+24),
        m.cmpabs(c,m.AFREE-24,m.APAY+28),
        m.cmpabs(c,m.AFREE-24,m.ABASE+m.MH_FREE),
    ]

    # Free using the original request sizes. FreeMem must round 1 -> 8 and
    # 9 -> 16 and restore region A exactly.
    free(m.APAY,1)
    free(m.APAY+8,9)
    fails += [
        m.cmpabs(c,m.APAY,m.ABASE+m.MH_FIRST),
        m.cmpabs(c,0,m.APAY),
        m.cmpabs(c,m.AFREE,m.APAY+4),
        m.cmpabs(c,m.AFREE,m.ABASE+m.MH_FREE),
    ]

    free(m.CPAY,m.CFREE)
    free(m.FAST_BASE,m.FAST_SIZE)
    avail(m.MEMF_FAST,m.FAST_SIZE+m.AFREE+m.CFREE)

    c+=m.mw(0x00f0,m.COLOR00); ok=m.branch(c,0x6000)
    bad=len(c); c+=m.mw(0x000f,m.COLOR00)
    idle=len(c); c+=bytes.fromhex('60FE')
    for fail in fails: m.patch(c,fail,bad)
    m.patch(c,ok,idle)
    if test_abs+len(c)>PROBE_END: raise ValueError('M2.29 runtime probe exceeds dedicated ROM window')
    if any(b != 0xff for b in image[test_abs:test_abs+len(c)]):
        raise ValueError('M2.29 runtime probe window is not unused')
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
    if len(sys.argv)!=2: raise SystemExit('usage: make_m2_29_rom.py OUTPUT')
    out=Path(sys.argv[1]); data=build(); out.write_bytes(data)
    print(f'M2.29 ROM built: {out} ({len(data)} bytes)')
