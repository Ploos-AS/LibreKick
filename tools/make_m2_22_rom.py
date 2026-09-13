#!/usr/bin/env python3
"""Build LibreKick M2.22: qualify whole-chunk removal from a non-head MemChunk."""
from pathlib import Path
import struct, sys
import make_m2_21_rom as p
import make_m2_17_rom as m

MARKER=b'LIBREKICK-M2.22\0EXEC-DYNAMIC-WHOLE-CHUNK-UNLINK\0'
IDENT=b'exec.library\0LibreKick M2.22 dynamic whole-chunk unlink slice 40.22\0'


def build():
    image=bytearray(p.build())

    # Chain an M2.22 probe after the M2.21 green path. M2.21 implemented the
    # whole-chunk path; this slice specifically qualifies the non-head relink
    # case where prev->mc_Next must bypass an exactly consumed free chunk.
    boot=image[8:0x0B00]
    sig=bytes.fromhex('33FC00F000DFF1806000')
    gp=boot.rfind(sig)
    if gp<0: raise ValueError('M2.21 final success gate not found')
    good_abs=8+gp; branch_pos=good_abs+8
    fail_sig=bytes.fromhex('33FC000F00DFF18060FE')
    fp=boot.find(fail_sig,gp)
    if fp<0: raise ValueError('M2.21 final fail gate not found')
    test_abs=8+fp+len(fail_sig)

    c=bytearray(); fails=[]
    def alloc(size,flags,expect):
        c.extend(bytes.fromhex('203C')+struct.pack('>I',size)+bytes.fromhex('223C')+struct.pack('>I',flags)+bytes.fromhex('4EAEFF3A'))
        fails.append(m.cmpd0(c,expect))
    def free(addr,size):
        c.extend(bytes.fromhex('227C')+struct.pack('>I',addr)+bytes.fromhex('203C')+struct.pack('>I',size)+bytes.fromhex('4EAEFF2E'))
    def avail(flags,expect):
        c.extend(bytes.fromhex('223C')+struct.pack('>I',flags)+bytes.fromhex('4EAEFF28'))
        fails.append(m.cmpd0(c,expect))

    # Exhaust static FAST, then lay out four dynamic allocations:
    # A0=$9020/$100, A1=$9120/$100, A2=$9220/$180, A3=$93a0/$100.
    # Free A0 and A2 only. The free list is then:
    #   $9020/$100 -> $9220/$180 -> $94a0/$b60
    # with A1 and A3 still live separators. Total mh_Free is $de0.
    alloc(m.FAST_SIZE,m.MEMF_FAST,m.FAST_BASE)
    alloc(0x100,m.MEMF_FAST,m.APAY)
    alloc(0x100,m.MEMF_FAST,m.APAY+0x100)
    alloc(0x180,m.MEMF_FAST,m.APAY+0x200)
    alloc(0x100,m.MEMF_FAST,m.APAY+0x380)
    free(m.APAY,0x100)
    free(m.APAY+0x200,0x180)

    tail_bytes=m.AFREE-0x480
    fails += [
        m.cmpabs(c,m.APAY,m.ABASE+m.MH_FIRST),
        m.cmpabs(c,m.APAY+0x200,m.APAY),
        m.cmpabs(c,0x100,m.APAY+4),
        m.cmpabs(c,m.APAY+0x480,m.APAY+0x200),
        m.cmpabs(c,0x180,m.APAY+0x204),
        m.cmpabs(c,m.AFREE-0x200,m.ABASE+m.MH_FREE),
    ]

    # Exact $180 request skips the $100 head and consumes the second free
    # chunk whole. The predecessor must now point directly to the unchanged
    # tail chunk. mh_Free drops by $180, but the tail chunk itself remains
    # $b60; these are deliberately distinct invariants.
    alloc(0x180,m.MEMF_FAST,m.APAY+0x200)
    fails += [
        m.cmpabs(c,m.APAY,m.ABASE+m.MH_FIRST),
        m.cmpabs(c,m.APAY+0x480,m.APAY),
        m.cmpabs(c,0x100,m.APAY+4),
        m.cmpabs(c,0,m.APAY+0x480),
        m.cmpabs(c,tail_bytes,m.APAY+0x484),
        m.cmpabs(c,m.AFREE-0x380,m.ABASE+m.MH_FREE),
    ]

    # Restore every live allocation. FreeMem must reinsert and coalesce all
    # chunks back to one complete free chunk at APAY.
    free(m.APAY+0x200,0x180)
    free(m.APAY+0x100,0x100)
    free(m.APAY+0x380,0x100)
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
    if test_abs+len(c)>=0x0B00: raise ValueError('M2.22 runtime probe exceeds bootstrap area')
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
    if len(sys.argv)!=2: raise SystemExit('usage: make_m2_22_rom.py OUTPUT')
    out=Path(sys.argv[1]); data=build(); out.write_bytes(data)
    print(f'M2.22 ROM built: {out} ({len(data)} bytes)')
