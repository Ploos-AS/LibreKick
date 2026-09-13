#!/usr/bin/env python3
"""Build LibreKick M2.21: dynamic AllocMem scans arbitrary MemChunk chains."""
from pathlib import Path
import struct, sys
import make_m2_20_rom as p
import make_m2_17_rom as m

MARKER=b'LIBREKICK-M2.21\0EXEC-DYNAMIC-MEMCHUNK-TRAVERSAL\0'
IDENT=b'exec.library\0LibreKick M2.21 dynamic MemChunk traversal slice 40.21\0'


def dynamic_alloc_core_code_m221():
    """D0=size, A0=MemHeader -> D0=block or NULL; first-fit across MemChunk chain."""
    q=bytearray(bytes.fromhex('2F012F022F032F042F092F0A2F0B'))  # d1-d4,a1-a3
    q+=bytes.fromhex('4A80'); bad0=m.branch(q,0x6700)
    q+=bytes.fromhex('0680000000070280FFFFFFF8')         # align request to 8
    q+=bytes.fromhex('2200')                               # d1=request
    q+=bytes.fromhex('22680010')                           # a1=mh_First
    q+=bytes.fromhex('267C00000000')                       # a3=prev=NULL

    loop=len(q)
    q+=bytes.fromhex('28094A84'); no_chunk=m.branch(q,0x6700) # d4=a1; tst.l d4
    q+=bytes.fromhex('24290004')                           # d2=current.bytes
    q+=bytes.fromhex('26029681')                           # d3=bytes-request
    too_small=m.branch(q,0x6500)                           # borrow -> next chunk
    q+=bytes.fromhex('0C8300000008'); whole=m.branch(q,0x6500)

    # Split selected chunk. Remainder replaces current in list.
    q+=bytes.fromhex('2449D5C1')                           # a2=current+request
    q+=bytes.fromhex('2491')                               # remainder.next=current.next
    q+=bytes.fromhex('25430004')                           # remainder.bytes=d3
    q+=bytes.fromhex('280B4A84'); split_head=m.branch(q,0x6700)
    q+=bytes.fromhex('268A'); split_linked=m.branch(q,0x6000) # prev.next=remainder
    sh=len(q); q+=bytes.fromhex('214A0010')                 # mh_First=remainder
    sl=len(q)
    q+=bytes.fromhex('2428001C94812142001C')               # mh_Free-=request
    q+=bytes.fromhex('2009'); split_done=m.branch(q,0x6000)

    # Consume whole selected chunk when remainder would be too small.
    wh=len(q)
    q+=bytes.fromhex('2451')                               # a2=current.next
    q+=bytes.fromhex('280B4A84'); whole_head=m.branch(q,0x6700)
    q+=bytes.fromhex('268A'); whole_linked=m.branch(q,0x6000)
    qh=len(q); q+=bytes.fromhex('214A0010')                 # mh_First=next
    ql=len(q)
    q+=bytes.fromhex('2628001C96822143001C')               # mh_Free-=chunk.bytes
    q+=bytes.fromhex('2009'); whole_done=m.branch(q,0x6000)

    # Advance through fragmented free list.
    adv=len(q)
    q+=bytes.fromhex('26492251')                           # prev=current; current=current.next
    again=m.branch(q,0x6000)

    bad=len(q); q+=bytes.fromhex('7000')
    out=len(q); q+=bytes.fromhex('265F245F225F281F261F241F221F4E75')

    m.patch(q,bad0,bad); m.patch(q,no_chunk,bad); m.patch(q,too_small,adv)
    m.patch(q,whole,wh); m.patch(q,split_head,sh); m.patch(q,split_linked,sl)
    m.patch(q,whole_head,qh); m.patch(q,whole_linked,ql)
    m.patch(q,split_done,out); m.patch(q,whole_done,out); m.patch(q,again,loop)
    return bytes(q)


def build():
    image=bytearray(p.build())

    # Replace M2.16's single-head dynamic allocator with a general first-fit
    # MemChunk-chain allocator. Keep the established internal ABI and slot.
    code=dynamic_alloc_core_code_m221()
    if len(code)>m.DYN_FREE_OFF-m.DYN_ALLOC_OFF:
        raise ValueError('M2.21 dynamic allocator exceeds fixed slot')
    image[m.DYN_ALLOC_OFF:m.DYN_FREE_OFF]=b'\xff'*(m.DYN_FREE_OFF-m.DYN_ALLOC_OFF)
    image[m.DYN_ALLOC_OFF:m.DYN_ALLOC_OFF+len(code)]=code

    # Chain an M2.21 probe after the M2.20 green path.
    boot=image[8:0x0B00]
    sig=bytes.fromhex('33FC00F000DFF1806000')
    gp=boot.rfind(sig)
    if gp<0: raise ValueError('M2.20 final success gate not found')
    good_abs=8+gp; branch_pos=good_abs+8
    fail_sig=bytes.fromhex('33FC000F00DFF18060FE')
    fp=boot.find(fail_sig,gp)
    if fp<0: raise ValueError('M2.20 final fail gate not found')
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

    # Exhaust static FAST, then fragment dynamic FAST A into two free chunks:
    # [APAY,$100] and [APAY+$200,$DE0], separated by one live $100 block.
    alloc(m.FAST_SIZE,m.MEMF_FAST,m.FAST_BASE)
    alloc(0x100,m.MEMF_FAST,m.APAY)
    alloc(0x100,m.MEMF_FAST,m.APAY+0x100)
    alloc(0x100,m.MEMF_FAST,m.APAY+0x200)
    free(m.APAY,0x100)
    free(m.APAY+0x200,0x100)
    fails += [m.cmpabs(c,m.APAY,m.ABASE+m.MH_FIRST),
              m.cmpabs(c,m.APAY+0x200,m.APAY),
              m.cmpabs(c,0x100,m.APAY+4),
              m.cmpabs(c,m.AFREE-0x100,m.ABASE+m.MH_FREE)]

    # First chunk is too small for $180; first-fit must continue to the second.
    alloc(0x180,m.MEMF_FAST,m.APAY+0x200)
    fails += [m.cmpabs(c,m.APAY,m.ABASE+m.MH_FIRST),
              m.cmpabs(c,m.APAY+0x380,m.APAY),
              m.cmpabs(c,0x100,m.APAY+4),
              m.cmpabs(c,m.AFREE-0x280,m.ABASE+m.MH_FREE)]

    # Restore all allocations and verify the dynamic region coalesces completely.
    free(m.APAY+0x200,0x180)
    free(m.APAY+0x100,0x100)
    fails += [m.cmpabs(c,m.APAY,m.ABASE+m.MH_FIRST),
              m.cmpabs(c,0,m.APAY),
              m.cmpabs(c,m.AFREE,m.APAY+4),
              m.cmpabs(c,m.AFREE,m.ABASE+m.MH_FREE)]
    free(m.FAST_BASE,m.FAST_SIZE)
    avail(m.MEMF_FAST,m.FAST_SIZE+m.AFREE+m.CFREE)

    c+=m.mw(0x00f0,m.COLOR00); ok=m.branch(c,0x6000)
    bad=len(c); c+=m.mw(0x000f,m.COLOR00)
    idle=len(c); c+=bytes.fromhex('60FE')
    for fail in fails: m.patch(c,fail,bad)
    m.patch(c,ok,idle)
    if test_abs+len(c)>=0x0B00: raise ValueError('M2.21 runtime probe exceeds bootstrap area')
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
    if len(sys.argv)!=2: raise SystemExit('usage: make_m2_21_rom.py OUTPUT')
    out=Path(sys.argv[1]); data=build(); out.write_bytes(data)
    print(f'M2.21 ROM built: {out} ({len(data)} bytes)')
