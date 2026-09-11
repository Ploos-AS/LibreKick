#!/usr/bin/env python3
"""Build LibreKick M2.9: general first-fit traversal across MemChunk free list."""
from pathlib import Path
import struct, sys
from make_m2_8_rom import (
    ROM_SIZE, ROM_BASE, SP, PC, EXEC_BASE, COLOR00, CIAA_PRA, CIAA_DDRA,
    MEMHDR, MEM_BASE, MEM_SIZE, MH_ATTR, MH_FIRST, MH_LOWER, MH_UPPER, MH_FREE,
    MARKER_OFF, IDENT_OFF, ml, mw, mb, bclr0, vector, branch, patch, cmpd0,
    cmpabs, ones, freemem_code, availmem_code, MEMF_CHIP, MEMF_TOTAL,
)
IDSTRING_ADDR=ROM_BASE+IDENT_OFF
FUNCS={198:ROM_BASE+0x0B00,210:ROM_BASE+0x0C00,216:ROM_BASE+0x0D00}


def allocmem_code():
    # D0=size, D1=requirements -> D0=memory or NULL.
    # Walk every MemChunk until the first fitting chunk is found. A3 tracks prev.
    q=bytearray(bytes.fromhex('2F012F022F032F082F092F0A2F0B'))
    q+=bytes.fromhex('4A80'); bad0=branch(q,0x6700)
    q+=bytes.fromhex('0680000000070280FFFFFFF8')           # align request to 8
    q+=bytes.fromhex('2200')                                 # d1=request size
    q+=bytes.fromhex('207900004810')                         # a0=current=head
    q+=bytes.fromhex('267C00000000')                         # a3=prev=NULL
    loop=len(q)
    q+=bytes.fromhex('26084A83'); exhausted=branch(q,0x6700) # current == NULL
    q+=bytes.fromhex('24280004')                             # d2=current.bytes
    q+=bytes.fromhex('20029081'); too_small=branch(q,0x6500) # remainder underflow
    q+=bytes.fromhex('0C8000000008'); whole=branch(q,0x6500) # remainder < 8
    # Split selected chunk. Replacement remainder stays in same list position.
    q+=bytes.fromhex('2448D5C1')                             # a2=current+request
    q+=bytes.fromhex('2490')                                 # remainder.next=current.next
    q+=bytes.fromhex('25400004')                             # remainder.bytes=d0
    q+=bytes.fromhex('260B4A83'); split_head=branch(q,0x6700)
    q+=bytes.fromhex('268A'); split_linked=branch(q,0x6000)  # prev.next=remainder
    sh=len(q); q+=bytes.fromhex('23CA00004810')               # mh_First=remainder
    sl=len(q)
    q+=bytes.fromhex('24390000481C948123C20000481C')       # mh_Free -= request
    q+=bytes.fromhex('2008'); done_split=branch(q,0x6000)
    # Whole selected chunk. Unlink it whether it is head or a later node.
    wh=len(q)
    q+=bytes.fromhex('2450')                                 # a2=current.next
    q+=bytes.fromhex('260B4A83'); whole_head=branch(q,0x6700)
    q+=bytes.fromhex('268A'); whole_linked=branch(q,0x6000)  # prev.next=current.next
    whh=len(q); q+=bytes.fromhex('23CA00004810')              # mh_First=current.next
    whl=len(q)
    q+=bytes.fromhex('20390000481C908223C00000481C')       # mh_Free -= whole bytes
    q+=bytes.fromhex('2008'); done_whole=branch(q,0x6000)
    # Too-small chunk: advance prev/current and continue first-fit search.
    nxt=len(q); q+=bytes.fromhex('26482050'); again=branch(q,0x6000)
    bad=len(q); q+=bytes.fromhex('7000')
    out=len(q); q+=bytes.fromhex('265F245F225F205F261F241F221F4E75')
    patch(q,bad0,bad); patch(q,exhausted,bad); patch(q,too_small,nxt)
    patch(q,whole,wh); patch(q,split_head,sh); patch(q,split_linked,sl)
    patch(q,whole_head,whh); patch(q,whole_linked,whl)
    patch(q,done_split,out); patch(q,done_whole,out); patch(q,again,loop)
    return bytes(q)


def build():
    image=bytearray([0xff])*ROM_SIZE; struct.pack_into('>II',image,0,SP,PC)
    c=bytearray(bytes.fromhex('46FC2700')); c+=mb(3,CIAA_DDRA); c+=bclr0(CIAA_PRA); c+=ml(EXEC_BASE,4)
    c+=ml(0,EXEC_BASE)+ml(0,EXEC_BASE+4)+mw(0x0900,EXEC_BASE+8)+ml(IDSTRING_ADDR,EXEC_BASE+10)
    c+=mw(0,EXEC_BASE+14)+mw(216,EXEC_BASE+16)+mw(34,EXEC_BASE+18)+mw(40,EXEC_BASE+20)+mw(9,EXEC_BASE+22)+ml(IDSTRING_ADDR,EXEC_BASE+24)+ml(0,EXEC_BASE+28)+mw(0,EXEC_BASE+32)
    for off,t in FUNCS.items(): c+=vector(t,EXEC_BASE-off)
    c+=mw(MEMF_CHIP,MEMHDR+MH_ATTR)+ml(MEM_BASE,MEMHDR+MH_FIRST)+ml(MEM_BASE,MEMHDR+MH_LOWER)+ml(MEM_BASE+MEM_SIZE,MEMHDR+MH_UPPER)+ml(MEM_SIZE,MEMHDR+MH_FREE)
    c+=ml(0,MEM_BASE)+ml(MEM_SIZE,MEM_BASE+4)
    c+=mw(0x0f00,COLOR00)+b'\x4d\xf9'+struct.pack('>I',EXEC_BASE)
    fails=[]
    def alloc(size,expect):
        nonlocal c
        c+=bytes.fromhex('203C')+struct.pack('>I',size)+bytes.fromhex('223C000000024EAEFF3A')
        fails.append(cmpd0(c,expect))
    def free(addr,size):
        nonlocal c
        c+=bytes.fromhex('227C')+struct.pack('>I',addr)+bytes.fromhex('203C')+struct.pack('>I',size)+bytes.fromhex('4EAEFF2E')
    # Scenario 1: head is too small; second chunk must be selected and split.
    alloc(0x100,MEM_BASE); alloc(0x200,MEM_BASE+0x100); alloc(0x100,MEM_BASE+0x300)
    free(MEM_BASE,0x100); free(MEM_BASE+0x300,0x100)
    # Free list: $5000/100 -> $5300/D00. Request 180 must skip head.
    fails.append(cmpabs(c,MEM_BASE,MEMHDR+MH_FIRST)); fails.append(cmpabs(c,MEM_BASE+0x300,MEM_BASE))
    alloc(0x180,MEM_BASE+0x300)
    fails.append(cmpabs(c,MEM_BASE+0x480,MEM_BASE)); fails.append(cmpabs(c,MEM_SIZE-0x480,MEM_BASE+0x484))
    c+=bytes.fromhex('223C000800004EAEFF28'); fails.append(cmpd0(c,0x0C80))
    free(MEM_BASE+0x300,0x180); free(MEM_BASE+0x100,0x200)
    fails.append(cmpabs(c,MEM_BASE,MEMHDR+MH_FIRST)); fails.append(cmpabs(c,0,MEM_BASE)); fails.append(cmpabs(c,MEM_SIZE,MEM_BASE+4))
    # Scenario 2: head is too small; second chunk is an exact whole-chunk match.
    alloc(0x100,MEM_BASE); alloc(0x200,MEM_BASE+0x100); free(MEM_BASE,0x100)
    alloc(0x0D00,MEM_BASE+0x300)
    fails.append(cmpabs(c,MEM_BASE,MEMHDR+MH_FIRST)); fails.append(cmpabs(c,0,MEM_BASE))
    c+=bytes.fromhex('223C000800004EAEFF28'); fails.append(cmpd0(c,0x0100))
    free(MEM_BASE+0x300,0x0D00); free(MEM_BASE+0x100,0x200)
    c+=bytes.fromhex('223C000800004EAEFF28'); fails.append(cmpd0(c,MEM_SIZE))
    fails.append(cmpabs(c,MEM_BASE,MEMHDR+MH_FIRST)); fails.append(cmpabs(c,0,MEM_BASE)); fails.append(cmpabs(c,MEM_SIZE,MEM_BASE+4))
    c+=mw(0x00f0,COLOR00); done=branch(c,0x6000); bad=len(c); c+=mw(0x000f,COLOR00); idle=len(c); c+=bytes.fromhex('60FE')
    for p in fails: patch(c,p,bad)
    patch(c,done,idle)
    if 8+len(c)>0x0B00: raise ValueError('bootstrap overlaps allocator routines')
    image[8:8+len(c)]=c
    routines={0x0B00:allocmem_code(),0x0C00:freemem_code(),0x0D00:availmem_code()}
    ordered=sorted(routines.items())
    for (off,code),(nxt,_) in zip(ordered,ordered[1:]+[(MARKER_OFF,b'')]):
        if off+len(code)>nxt: raise ValueError(f'routine overlap at {off:x}')
        image[off:off+len(code)]=code
    marker=b'LIBREKICK-M2.9\0EXEC-ALLOCMEM-FIRST-FIT\0'
    ident=b'exec.library\0LibreKick M2.9 general first-fit allocator slice 40.9\0'
    image[MARKER_OFF:MARKER_OFF+len(marker)]=marker; image[IDENT_OFF:IDENT_OFF+len(ident)]=ident
    struct.pack_into('>I',image,ROM_SIZE-4,0); total=0
    for o in range(0,ROM_SIZE-4,4): total=ones(total,struct.unpack_from('>I',image,o)[0])
    total=(total&0xffffffff)+(total>>32); struct.pack_into('>I',image,ROM_SIZE-4,(~total)&0xffffffff)
    return image

if __name__=='__main__':
    if len(sys.argv)!=2: raise SystemExit('usage: make_m2_9_rom.py OUTPUT')
    out=Path(sys.argv[1]); data=build(); out.write_bytes(data); print(f'M2.9 ROM built: {out} ({len(data)} bytes)')
