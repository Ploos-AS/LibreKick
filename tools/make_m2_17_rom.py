#!/usr/bin/env python3
"""Build LibreKick M2.17: FreeMem routing across linked dynamic MemHeaders.

M2.17 keeps the M2.16 linked dynamic AllocMem traversal and extends FreeMem so
blocks are routed by address to the owning dynamic MemHeader. A generic dynamic
free core performs sorted MemChunk insertion plus successor/predecessor
coalescing relative to the selected header.
"""
from pathlib import Path
import struct, sys
from make_m2_16_rom import *

MARKER_OFF=0x2000
IDENT_OFF=0x2080
NAME_A_OFF=0x20E0
NAME_B_OFF=0x2100
NAME_C_OFF=0x2120
IDSTRING_ADDR=ROM_BASE+IDENT_OFF
NAME_A_ADDR=ROM_BASE+NAME_A_OFF
NAME_B_ADDR=ROM_BASE+NAME_B_OFF
NAME_C_ADDR=ROM_BASE+NAME_C_OFF
DYN_FREE_OFF=0x1800
FUNCS={198:ROM_BASE+0x0B00,210:ROM_BASE+0x0C00,216:ROM_BASE+0x0D00,618:ROM_BASE+ADDMEM_OFF}


def dynamic_free_core_code():
    """A0=MemHeader, A1=block, D0=size. Sorted insert + bidirectional merge."""
    q=bytearray(bytes.fromhex('2F012F022F032F082F0A2F0B2F0C')) # d1,d2,d3,a0,a2,a3,a4
    q+=bytes.fromhex('2848')                                 # a4=header
    q+=bytes.fromhex('22094A81'); ret0=branch(q,0x6700)
    q+=bytes.fromhex('4A80'); ret1=branch(q,0x6700)
    q+=bytes.fromhex('0680000000070280FFFFFFF8')           # align size
    q+=bytes.fromhex('2400')                                 # d2=size
    q+=bytes.fromhex('206C0010')                             # a0=mh_First(a4)
    q+=bytes.fromhex('267C00000000')                         # a3=prev=NULL
    loop=len(q)
    q+=bytes.fromhex('22084A81'); ins_end=branch(q,0x6700)
    q+=bytes.fromhex('2609B283'); ins_before=branch(q,0x6200) # current > new
    q+=bytes.fromhex('26482050'); again=branch(q,0x6000)
    ins=len(q)
    q+=bytes.fromhex('2288')                                 # new.next=current
    q+=bytes.fromhex('23420004')                             # new.bytes=size
    q+=bytes.fromhex('220B4A81'); at_head=branch(q,0x6700)
    q+=bytes.fromhex('2689'); linked=branch(q,0x6000)
    ah=len(q); q+=bytes.fromhex('29490010')                   # mh_First(a4)=new
    lk=len(q)
    q+=bytes.fromhex('222C001CD2822941001C')                 # mh_Free += size
    # successor merge: new + size == current
    q+=bytes.fromhex('22084A81'); no_next=branch(q,0x6700)
    q+=bytes.fromhex('2449D5C2')
    q+=bytes.fromhex('220A2608B283'); no_next2=branch(q,0x6600)
    q+=bytes.fromhex('22280004D3A90004')
    q+=bytes.fromhex('2450228A')
    nn=len(q)
    # predecessor merge: prev + prev.bytes == new
    q+=bytes.fromhex('220B4A81'); no_prev=branch(q,0x6700)
    q+=bytes.fromhex('244B222B0004D5C1')
    q+=bytes.fromhex('220A2609B283'); no_prev2=branch(q,0x6600)
    q+=bytes.fromhex('22290004D3AB0004')
    q+=bytes.fromhex('2451268A')
    np=len(q)
    out=len(q); q+=bytes.fromhex('285F265F245F205F261F241F221F4E75')
    patch(q,ret0,out); patch(q,ret1,out); patch(q,ins_end,ins); patch(q,ins_before,ins)
    patch(q,again,loop); patch(q,at_head,ah); patch(q,linked,lk)
    patch(q,no_next,nn); patch(q,no_next2,nn); patch(q,no_prev,np); patch(q,no_prev2,np)
    return bytes(q)


def free_wrapper_code_m217():
    """Route FreeMem to static CHIP/FAST or the owning linked dynamic header."""
    q=bytearray(bytes.fromhex('2F012F022F08'))               # d1,d2,a0
    q+=bytes.fromhex('2209')                                 # d1=block address

    # Static CHIP range.
    q+=bytes.fromhex('0C81')+struct.pack('>I',MEM_BASE); below_chip=branch(q,0x6500)
    q+=bytes.fromhex('0C81')+struct.pack('>I',MEM_BASE+MEM_SIZE); chip=branch(q,0x6500)
    bc=len(q)
    # Static FAST range.
    q+=bytes.fromhex('0C81')+struct.pack('>I',FAST_BASE); dyn_from_low=branch(q,0x6500)
    q+=bytes.fromhex('0C81')+struct.pack('>I',FAST_BASE+FAST_SIZE); fast=branch(q,0x6500)
    dyn_entry=len(q)
    q+=bytes.fromhex('2079')+struct.pack('>I',DYN_HEAD)
    loop=len(q)
    q+=bytes.fromhex('24084A82'); done_null=branch(q,0x6700)
    q+=bytes.fromhex('24280014B282'); advance_low=branch(q,0x6500) # block < mh_Lower
    q+=bytes.fromhex('24280018B282'); found=branch(q,0x6500)       # block < mh_Upper
    adv=len(q); q+=bytes.fromhex('2050'); again=branch(q,0x6000)
    fd=len(q); q+=bytes.fromhex('4EB9')+struct.pack('>I',ROM_BASE+DYN_FREE_OFF); done_dyn=branch(q,0x6000)
    ch=len(q); q+=bytes.fromhex('4EB9')+struct.pack('>I',ROM_BASE+CHIP_FREE_OFF); done_chip=branch(q,0x6000)
    fa=len(q); q+=bytes.fromhex('4EB9')+struct.pack('>I',ROM_BASE+FAST_FREE_OFF)
    done=len(q); q+=bytes.fromhex('205F241F221F4E75')

    patch(q,below_chip,bc); patch(q,chip,ch); patch(q,dyn_from_low,dyn_entry); patch(q,fast,fa)
    patch(q,done_null,done); patch(q,advance_low,adv); patch(q,found,fd); patch(q,again,loop)
    patch(q,done_dyn,done); patch(q,done_chip,done)
    return bytes(q)


def build():
    image=bytearray([0xff])*ROM_SIZE
    struct.pack_into('>II',image,0,SP,PC)
    c=bytearray(bytes.fromhex('46FC2700'))
    c+=mb(3,CIAA_DDRA)+bclr0(CIAA_PRA)+ml(EXEC_BASE,4)
    c+=ml(0,EXEC_BASE)+ml(0,EXEC_BASE+4)+mw(0x0900,EXEC_BASE+8)+ml(IDSTRING_ADDR,EXEC_BASE+10)
    c+=mw(0,EXEC_BASE+14)+mw(618,EXEC_BASE+16)+mw(34,EXEC_BASE+18)+mw(40,EXEC_BASE+20)+mw(17,EXEC_BASE+22)+ml(IDSTRING_ADDR,EXEC_BASE+24)+ml(0,EXEC_BASE+28)+mw(0,EXEC_BASE+32)
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
    def free(addr,size):
        nonlocal c
        c+=bytes.fromhex('227C')+struct.pack('>I',addr)+bytes.fromhex('203C')+struct.pack('>I',size)+bytes.fromhex('4EAEFF2E')

    add(ABASE,ASIZE,MEMF_FAST,5,NAME_A_ADDR)
    add(BBASE,BSIZE,MEMF_CHIP,3,NAME_B_ADDR)
    add(CBASE,CSIZE,MEMF_FAST,7,NAME_C_ADDR)
    fails += [cmpabs(c,CBASE,DYN_HEAD),cmpabs(c,BBASE,CBASE),cmpabs(c,ABASE,BBASE)]

    # Force FAST allocation through C -> B -> A, then free it through public
    # FreeMem and require A's single free chunk to be fully restored.
    alloc(FAST_SIZE,MEMF_FAST,FAST_BASE)
    alloc(0x100,MEMF_FAST|MEMF_CLEAR,APAY)
    fails += [cmpabs(c,APAY+0x100,ABASE+MH_FIRST),cmpabs(c,AFREE-0x100,ABASE+MH_FREE)]
    free(APAY,0x100)
    fails += [cmpabs(c,APAY,ABASE+MH_FIRST),cmpabs(c,0,APAY),cmpabs(c,AFREE,APAY+4),cmpabs(c,AFREE,ABASE+MH_FREE)]
    avail(MEMF_FAST,AFREE+CFREE)

    # Exhaust static CHIP so allocation comes from middle dynamic header B;
    # freeing must locate B by mh_Lower/mh_Upper rather than list position.
    alloc(MEM_SIZE,MEMF_CHIP,MEM_BASE)
    alloc(0x100,MEMF_CHIP,BBASE+32)
    fails += [cmpabs(c,BBASE+32+0x100,BBASE+MH_FIRST),cmpabs(c,BFREE-0x100,BBASE+MH_FREE)]
    free(BBASE+32,0x100)
    fails += [cmpabs(c,BBASE+32,BBASE+MH_FIRST),cmpabs(c,0,BBASE+32),cmpabs(c,BFREE,BBASE+36),cmpabs(c,BFREE,BBASE+MH_FREE)]
    avail(MEMF_CHIP,BFREE)

    # Static FreeMem routing remains intact.
    free(FAST_BASE,FAST_SIZE); free(MEM_BASE,MEM_SIZE)
    avail(MEMF_FAST,FAST_SIZE+AFREE+CFREE)
    avail(MEMF_CHIP,MEM_SIZE+BFREE)

    c+=mw(0x00f0,COLOR00); good=branch(c,0x6000)
    bad=len(c); c+=mw(0x000f,COLOR00)
    idle=len(c); c+=bytes.fromhex('60FE')
    for p in fails: patch(c,p,bad)
    patch(c,good,idle)
    if 8+len(c)>0x0B00: raise ValueError('bootstrap overlaps M2.17 routines')
    image[8:8+len(c)]=c

    fa=relocate_region(allocmem_core_code(),MEMHDR,FAST_HDR)
    ff=relocate_region(freemem_code(),MEMHDR,FAST_HDR)
    routines={
        0x0B00:alloc_wrapper_code(), 0x0C00:free_wrapper_code_m217(), 0x0D00:avail_wrapper_code(),
        CHIP_ALLOC_OFF:allocmem_core_code(), CHIP_FREE_OFF:freemem_code(),
        FAST_ALLOC_OFF:fa, FAST_FREE_OFF:ff,
        CHIP_LARGEST_OFF:largest_code(MEMHDR), FAST_LARGEST_OFF:largest_code(FAST_HDR),
        ADDMEM_OFF:addmemlist_code(), BASE_AVAIL_OFF:base_avail_code(),
        DYN_ALLOC_OFF:dynamic_alloc_core_code(), DYN_FREE_OFF:dynamic_free_core_code(),
    }
    ordered=sorted(routines.items())
    for (off,code),(nxt,_) in zip(ordered,ordered[1:]+[(MARKER_OFF,b'')]):
        if off+len(code)>nxt: raise ValueError(f'overlap {off:x}')
        image[off:off+len(code)]=code

    marker=b'LIBREKICK-M2.17\0EXEC-DYNAMIC-FREEMEM-ROUTING\0'
    ident=b'exec.library\0LibreKick M2.17 dynamic FreeMem routing slice 40.17\0'
    name_a=b'M2.17 dynamic FAST A\0'; name_b=b'M2.17 dynamic CHIP B\0'; name_c=b'M2.17 dynamic FAST C small\0'
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
    if len(sys.argv)!=2: raise SystemExit('usage: make_m2_17_rom.py OUTPUT')
    out=Path(sys.argv[1]); data=build(); out.write_bytes(data)
    print(f'M2.17 ROM built: {out} ({len(data)} bytes)')
