#!/usr/bin/env python3
"""Build LibreKick M2.23: qualify whole-chunk removal from MemChunk head."""
from pathlib import Path
import struct, sys
import make_m2_22_rom as p
import make_m2_17_rom as m

MARKER=b'LIBREKICK-M2.23\0EXEC-DYNAMIC-HEAD-WHOLE-CHUNK\0'
IDENT=b'exec.library\0LibreKick M2.23 dynamic head whole-chunk slice 40.23\0'


def build():
    image=bytearray(p.build())

    # Chain an M2.23 probe after the M2.22 green path. M2.22 qualified the
    # non-head unlink path; this slice qualifies the complementary mh_First
    # replacement path when an exact-size request consumes the head chunk.
    boot=image[8:0x0B00]
    sig=bytes.fromhex('33FC00F000DFF1806000')
    gp=boot.rfind(sig)
    if gp<0: raise ValueError('M2.22 final success gate not found')
    good_abs=8+gp; branch_pos=good_abs+8
    fail_sig=bytes.fromhex('33FC000F00DFF18060FE')
    fp=boot.find(fail_sig,gp)
    if fp<0: raise ValueError('M2.22 final fail gate not found')
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

    # Exhaust static FAST and create a free-list head that is exactly $180.
    # Layout after allocations:
    # A0=$9020/$180, A1=$91a0/$100, A2=$92a0/$100, tail=$93a0/$c60.
    # Freeing A0 yields:
    #   $9020/$180 -> $93a0/$c60
    # while A1/A2 remain live separators.
    alloc(m.FAST_SIZE,m.MEMF_FAST,m.FAST_BASE)
    alloc(0x180,m.MEMF_FAST,m.APAY)
    alloc(0x100,m.MEMF_FAST,m.APAY+0x180)
    alloc(0x100,m.MEMF_FAST,m.APAY+0x280)
    free(m.APAY,0x180)

    fails += [
        m.cmpabs(c,m.APAY,m.ABASE+m.MH_FIRST),
        m.cmpabs(c,m.APAY+0x380,m.APAY),
        m.cmpabs(c,0x180,m.APAY+4),
        m.cmpabs(c,0,m.APAY+0x380),
        m.cmpabs(c,m.AFREE-0x380,m.APAY+0x384),
        m.cmpabs(c,m.AFREE-0x200,m.ABASE+m.MH_FREE),
    ]

    # Exact $180 request consumes the head whole. mh_First must become the
    # existing tail chunk directly; no split node is created.
    alloc(0x180,m.MEMF_FAST,m.APAY)
    fails += [
        m.cmpabs(c,m.APAY+0x380,m.ABASE+m.MH_FIRST),
        m.cmpabs(c,0,m.APAY+0x380),
        m.cmpabs(c,m.AFREE-0x380,m.APAY+0x384),
        m.cmpabs(c,m.AFREE-0x380,m.ABASE+m.MH_FREE),
    ]

    # Restore all allocations and require complete coalescing.
    free(m.APAY,0x180)
    free(m.APAY+0x180,0x100)
    free(m.APAY+0x280,0x100)
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
    if test_abs+len(c)>=0x0B00: raise ValueError('M2.23 runtime probe exceeds bootstrap area')
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
    if len(sys.argv)!=2: raise SystemExit('usage: make_m2_23_rom.py OUTPUT')
    out=Path(sys.argv[1]); data=build(); out.write_bytes(data)
    print(f'M2.23 ROM built: {out} ({len(data)} bytes)')
