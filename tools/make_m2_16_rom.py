#!/usr/bin/env python3
"""Build LibreKick M2.16: AllocMem traversal across linked dynamic MemHeaders.

This slice keeps the M2.15 linked AddMemList/AvailMem model and extends
AllocMem so a static-region miss walks every dynamically registered MemHeader
with matching attributes. A generic dynamic allocator receives the selected
MemHeader in A0, avoiding fixed-address relocation for dynamic regions.
"""
from pathlib import Path
import struct, sys
from make_m2_15_rom import *

MARKER_OFF=0x1E00
IDENT_OFF=0x1E80
NAME_A_OFF=0x1EE0
NAME_B_OFF=0x1F00
NAME_C_OFF=0x1F20
IDSTRING_ADDR=ROM_BASE+IDENT_OFF
NAME_A_ADDR=ROM_BASE+NAME_A_OFF
NAME_B_ADDR=ROM_BASE+NAME_B_OFF
NAME_C_ADDR=ROM_BASE+NAME_C_OFF
CBASE=0x0000B000
CSIZE=0x0100
CFREE=CSIZE-32
CPAY=CBASE+32
DYN_ALLOC_OFF=0x1600
FUNCS={198:ROM_BASE+0x0B00,210:ROM_BASE+0x0C00,216:ROM_BASE+0x0D00,618:ROM_BASE+ADDMEM_OFF}


def dynamic_alloc_core_code():
    """D0=size, A0=MemHeader -> D0=block or NULL.

    M2.16 qualifies the common fresh/single-head dynamic-region case while the
    public wrapper itself is fully linked-header aware. Later slices can extend
    this core to arbitrary MemChunk chains without changing the routing ABI.
    """
    q=bytearray(bytes.fromhex('2F012F022F032F092F0A'))      # d1,d2,d3,a1,a2
    q+=bytes.fromhex('4A80'); bad0=branch(q,0x6700)
    q+=bytes.fromhex('0680000000070280FFFFFFF8')           # align request to 8
    q+=bytes.fromhex('2200')                                 # d1=request
    q+=bytes.fromhex('22680010')                             # a1=mh_First(a0)
    q+=bytes.fromhex('20094A80'); empty=branch(q,0x6700)
    q+=bytes.fromhex('24290004')                             # d2=chunk.bytes
    q+=bytes.fromhex('26029681'); too_small=branch(q,0x6500) # d3=bytes-request; borrow
    q+=bytes.fromhex('0C8300000008'); whole=branch(q,0x6500)

    # Split the head chunk: replacement remainder becomes mh_First.
    q+=bytes.fromhex('2449D5C1')                             # a2=a1+request
    q+=bytes.fromhex('2491')                                 # remainder.next=chunk.next
    q+=bytes.fromhex('25430004')                             # remainder.bytes=d3
    q+=bytes.fromhex('214A0010')                             # mh_First=a2
    q+=bytes.fromhex('2428001C94812142001C')                 # mh_Free-=request
    q+=bytes.fromhex('2009'); done_split=branch(q,0x6000)

    # If the tail remainder would be <8 bytes, consume the whole head chunk.
    wh=len(q)
    q+=bytes.fromhex('2451')                                 # a2=chunk.next
    q+=bytes.fromhex('214A0010')                             # mh_First=a2
    q+=bytes.fromhex('2628001C96822143001C')                 # mh_Free-=chunk.bytes
    q+=bytes.fromhex('2009'); done_whole=branch(q,0x6000)

    bad=len(q); q+=bytes.fromhex('7000')
    out=len(q); q+=bytes.fromhex('245F225F261F241F221F4E75')
    patch(q,bad0,bad); patch(q,empty,bad); patch(q,too_small,bad)
    patch(q,whole,wh); patch(q,done_split,out); patch(q,done_whole,out)
    return bytes(q)


def alloc_wrapper_code():
    """Route AllocMem through static region, then linked dynamic MemHeaders."""
    q=bytearray(bytes.fromhex('2F022F032F042F082F09'))      # d2,d3,d4,a0,a1
    q+=bytes.fromhex('24002601')                             # d2=size d3=requirements

    # Select static preferred region; CHIP|FAST is unsatisfiable.
    q+=bytes.fromhex('08030002'); fast=branch(q,0x6600)
    q+=bytes.fromhex('4EB9')+struct.pack('>I',ROM_BASE+CHIP_ALLOC_OFF)
    q+=bytes.fromhex('4A80'); got_chip=branch(q,0x6600)
    dyn_entry=branch(q,0x6000)

    f=len(q)
    q+=bytes.fromhex('08030001'); reject=branch(q,0x6600)
    q+=bytes.fromhex('4EB9')+struct.pack('>I',ROM_BASE+FAST_ALLOC_OFF)
    q+=bytes.fromhex('4A80'); got_fast=branch(q,0x6600)

    # Static miss: walk dynamic MemHeaders from DYN_HEAD. For no explicit
    # region bit, retain the existing deterministic CHIP preference.
    de=len(q)
    q+=bytes.fromhex('2079')+struct.pack('>I',DYN_HEAD)
    loop=len(q)
    q+=bytes.fromhex('20084A80'); no_dyn=branch(q,0x6700)
    q+=bytes.fromhex('78003828000E')                         # d4=zero-extended attrs.w
    q+=bytes.fromhex('08030002'); want_fast=branch(q,0x6600)
    q+=bytes.fromhex('08040001'); advance_chip=branch(q,0x6700)
    try_dyn=branch(q,0x6000)
    wf=len(q)
    q+=bytes.fromhex('08040002'); advance_fast=branch(q,0x6700)
    td=len(q)
    q+=bytes.fromhex('2248')                                 # a1=current header for callee preservation
    q+=bytes.fromhex('20022203')                             # restore size/requirements
    q+=bytes.fromhex('4EB9')+struct.pack('>I',ROM_BASE+DYN_ALLOC_OFF)
    q+=bytes.fromhex('4A80'); dyn_ok=branch(q,0x6600)
    # Advance from A0, which always holds the current MemHeader. The previous
    # version advanced via A1; on an attribute-mismatch path A1 still referred
    # to the prior header, so C -> B then repeatedly reloaded B and never
    # reached A. The initial diagnostic red screen therefore remained forever.
    adv=len(q); q+=bytes.fromhex('2050')                     # a0=current->ln_Succ
    again=branch(q,0x6000)

    # Shared success path performs MEMF_CLEAR over the aligned requested size.
    success=len(q)
    q+=bytes.fromhex('08030010'); done_plain=branch(q,0x6700)
    q+=bytes.fromhex('2040')                                 # a0=result
    q+=bytes.fromhex('0682000000070282FFFFFFF8')             # align original size
    clear_loop=len(q); q+=bytes.fromhex('42985982'); more=branch(q,0x6600)
    done=len(q); q+=bytes.fromhex('225F205F281F261F241F4E75')
    bad=len(q); q+=bytes.fromhex('7000'); bad_done=branch(q,0x6000)

    patch(q,fast,f); patch(q,reject,bad)
    patch(q,got_chip,success); patch(q,got_fast,success); patch(q,dyn_ok,success)
    patch(q,dyn_entry,de); patch(q,no_dyn,bad)
    patch(q,want_fast,wf); patch(q,advance_chip,adv); patch(q,try_dyn,td); patch(q,advance_fast,adv)
    patch(q,again,loop); patch(q,done_plain,done); patch(q,more,clear_loop); patch(q,bad_done,done)
    return bytes(q)


def cmpabsw(c,v,a):
    c+=bytes.fromhex('0C79')+struct.pack('>H',v&0xffff)+struct.pack('>I',a)
    return branch(c,0x6600)


def build():
    image=bytearray([0xff])*ROM_SIZE
    struct.pack_into('>II',image,0,SP,PC)
    c=bytearray(bytes.fromhex('46FC2700'))
    c+=mb(3,CIAA_DDRA)+bclr0(CIAA_PRA)+ml(EXEC_BASE,4)
    c+=ml(0,EXEC_BASE)+ml(0,EXEC_BASE+4)+mw(0x0900,EXEC_BASE+8)+ml(IDSTRING_ADDR,EXEC_BASE+10)
    c+=mw(0,EXEC_BASE+14)+mw(618,EXEC_BASE+16)+mw(34,EXEC_BASE+18)+mw(40,EXEC_BASE+20)+mw(16,EXEC_BASE+22)+ml(IDSTRING_ADDR,EXEC_BASE+24)+ml(0,EXEC_BASE+28)+mw(0,EXEC_BASE+32)
    for off,t in FUNCS.items(): c+=vector(t,EXEC_BASE-off)

    c+=mw(MEMF_CHIP,MEMHDR+MH_ATTR)+ml(MEM_BASE,MEMHDR+MH_FIRST)+ml(MEM_BASE,MEMHDR+MH_LOWER)+ml(MEM_BASE+MEM_SIZE,MEMHDR+MH_UPPER)+ml(MEM_SIZE,MEMHDR+MH_FREE)+ml(0,MEM_BASE)+ml(MEM_SIZE,MEM_BASE+4)
    c+=mw(MEMF_FAST,FAST_HDR+MH_ATTR)+ml(FAST_BASE,FAST_HDR+MH_FIRST)+ml(FAST_BASE,FAST_HDR+MH_LOWER)+ml(FAST_BASE+FAST_SIZE,FAST_HDR+MH_UPPER)+ml(FAST_SIZE,FAST_HDR+MH_FREE)+ml(0,FAST_BASE)+ml(FAST_SIZE,FAST_BASE+4)
    c+=ml(0,DYN_HEAD)+mw(0x0f00,COLOR00)+b'\x4d\xf9'+struct.pack('>I',EXEC_BASE)

    fails=[]
    def avail(flags,expect):
        nonlocal c
        c+=bytes.fromhex('223C')+struct.pack('>I',flags)+bytes.fromhex('4EAEFF28')
        fails.append(cmpd0(c,expect))
    def add(base,size,attrs,pri,name):
        nonlocal c
        c+=bytes.fromhex('203C')+struct.pack('>I',size)+bytes.fromhex('223C')+struct.pack('>I',attrs)+bytes.fromhex('243C')+struct.pack('>I',pri)+bytes.fromhex('207C')+struct.pack('>I',base)+bytes.fromhex('227C')+struct.pack('>I',name)+bytes.fromhex('4EAEFD96')
    def alloc(size,flags,expect):
        nonlocal c
        c+=bytes.fromhex('203C')+struct.pack('>I',size)+bytes.fromhex('223C')+struct.pack('>I',flags)+bytes.fromhex('4EAEFF3A')
        fails.append(cmpd0(c,expect))

    # Three dynamic headers: newest C is FAST but too small for the qualified
    # request; B is CHIP; A is FAST and large enough. This forces C -> B -> A.
    add(ABASE,ASIZE,MEMF_FAST,5,NAME_A_ADDR)
    add(BBASE,BSIZE,MEMF_CHIP,3,NAME_B_ADDR)
    add(CBASE,CSIZE,MEMF_FAST,7,NAME_C_ADDR)
    fails += [cmpabs(c,CBASE,DYN_HEAD),cmpabs(c,BBASE,CBASE),cmpabs(c,ABASE,BBASE),cmpabs(c,0,ABASE)]
    fails += [cmpabs(c,CBASE,BBASE+4),cmpabs(c,BBASE,ABASE+4)]
    fails += [cmpabs(c,CFREE,CBASE+MH_FREE),cmpabs(c,AFREE,ABASE+MH_FREE)]
    avail(MEMF_FAST,FAST_SIZE+AFREE+CFREE)

    # Exhaust static FAST, then request 0x100 FAST|CLEAR. C has only 0xe0 free,
    # B mismatches attributes, so dynamic traversal must allocate from A.
    alloc(FAST_SIZE,MEMF_FAST,FAST_BASE)
    alloc(0x100,MEMF_FAST|MEMF_CLEAR,APAY)
    for off in range(0,0x100,4): fails.append(cmpabs(c,0,APAY+off))
    fails += [cmpabs(c,APAY+0x100,ABASE+MH_FIRST),cmpabs(c,AFREE-0x100,ABASE+MH_FREE)]
    fails += [cmpabs(c,CPAY,CBASE+MH_FIRST),cmpabs(c,CFREE,CBASE+MH_FREE)]
    avail(MEMF_FAST,(AFREE-0x100)+CFREE)
    avail(MEMF_CHIP,MEM_SIZE+BFREE)

    c+=mw(0x00f0,COLOR00); good=branch(c,0x6000)
    bad=len(c); c+=mw(0x000f,COLOR00)
    idle=len(c); c+=bytes.fromhex('60FE')
    for p in fails: patch(c,p,bad)
    patch(c,good,idle)
    if 8+len(c)>0x0B00: raise ValueError('bootstrap overlaps M2.16 routines')
    image[8:8+len(c)]=c

    fa=relocate_region(allocmem_core_code(),MEMHDR,FAST_HDR)
    ff=relocate_region(freemem_code(),MEMHDR,FAST_HDR)
    routines={
        0x0B00:alloc_wrapper_code(),
        0x0C00:free_wrapper_code(),
        0x0D00:avail_wrapper_code(),
        CHIP_ALLOC_OFF:allocmem_core_code(), CHIP_FREE_OFF:freemem_code(),
        FAST_ALLOC_OFF:fa, FAST_FREE_OFF:ff,
        CHIP_LARGEST_OFF:largest_code(MEMHDR), FAST_LARGEST_OFF:largest_code(FAST_HDR),
        ADDMEM_OFF:addmemlist_code(), BASE_AVAIL_OFF:base_avail_code(),
        DYN_ALLOC_OFF:dynamic_alloc_core_code(),
    }
    ordered=sorted(routines.items())
    for (off,code),(nxt,_) in zip(ordered,ordered[1:]+[(MARKER_OFF,b'')]):
        if off+len(code)>nxt: raise ValueError(f'overlap {off:x}')
        image[off:off+len(code)]=code

    marker=b'LIBREKICK-M2.16\0EXEC-DYNAMIC-ALLOCMEM-TRAVERSAL\0'
    ident=b'exec.library\0LibreKick M2.16 dynamic AllocMem traversal slice 40.16\0'
    name_a=b'M2.16 dynamic FAST A\0'; name_b=b'M2.16 dynamic CHIP B\0'; name_c=b'M2.16 dynamic FAST C small\0'
    image[MARKER_OFF:MARKER_OFF+len(marker)]=marker
    image[IDENT_OFF:IDENT_OFF+len(ident)]=ident
    image[NAME_A_OFF:NAME_A_OFF+len(name_a)]=name_a
    image[NAME_B_OFF:NAME_B_OFF+len(name_b)]=name_b
    image[NAME_C_OFF:NAME_C_OFF+len(name_c)]=name_c

    struct.pack_into('>I',image,ROM_SIZE-4,0); total=0
    for o in range(0,ROM_SIZE-4,4): total=ones(total,struct.unpack_from('>I',image,o)[0])
    total=(total&0xffffffff)+(total>>32)
    struct.pack_into('>I',image,ROM_SIZE-4,(~total)&0xffffffff)
    return image

if __name__=='__main__':
    if len(sys.argv)!=2: raise SystemExit('usage: make_m2_16_rom.py OUTPUT')
    out=Path(sys.argv[1]); data=build(); out.write_bytes(data)
    print(f'M2.16 ROM built: {out} ({len(data)} bytes)')
