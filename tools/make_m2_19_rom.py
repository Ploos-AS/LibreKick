#!/usr/bin/env python3
"""Build LibreKick M2.19: priority-sorted dynamic AddMemList insertion."""
from pathlib import Path
import struct, sys
import make_m2_18_rom as p
import make_m2_17_rom as m

MARKER=b'LIBREKICK-M2.19\0EXEC-PRIORITY-ADDMEMLIST\0'
IDENT=b'exec.library\0LibreKick M2.19 priority AddMemList slice 40.19\0'


def addmemlist_code_m219():
    """Insert dynamic MemHeaders by signed ln_Pri, descending; equal priority is FIFO."""
    q=bytearray(bytes.fromhex('2F032F042F052F0A2F0B2F0C')) # d3,d4,d5,a2,a3,a4
    q+=bytes.fromhex('260028482A02488548C5')        # d3=size,a4=base,d5=sign-extended pri
    q+=bytes.fromhex('0C8300000028'); small=m.branch(q,0x6500)

    # Initialize Node/MemHeader and the first MemChunk, but do not publish links yet.
    q+=bytes.fromhex('429042A80004114200092149000A3141000E')
    q+=bytes.fromhex('45E80020214A0010214A0014')
    q+=bytes.fromhex('2808D88321440018')
    q+=bytes.fromhex('0483000000202143001C429225430004')

    # A2=current, A3=previous. Find first node whose signed priority is lower.
    q+=bytes.fromhex('2479')+struct.pack('>I',m.DYN_HEAD)
    q+=bytes.fromhex('267C00000000')
    loop=len(q)
    q+=bytes.fromhex('280A4A84'); at_end=m.branch(q,0x6700)
    q+=bytes.fromhex('182A0009488448C4B885')        # d4=signext current ln_Pri; cmp d5,d4
    before=m.branch(q,0x6D00)                              # BLT: current < new
    q+=bytes.fromhex('264A2452'); again=m.branch(q,0x6000)

    ins=len(q)
    q+=bytes.fromhex('288A294B0004')                      # new.succ=current; new.pred=prev
    q+=bytes.fromhex('280B4A84'); no_prev=m.branch(q,0x6700)
    q+=bytes.fromhex('268C'); linked_prev=m.branch(q,0x6000) # prev.succ=new
    head=len(q); q+=bytes.fromhex('23CC')+struct.pack('>I',m.DYN_HEAD)
    after_prev=len(q)
    q+=bytes.fromhex('280A4A84'); no_next=m.branch(q,0x6700)
    q+=bytes.fromhex('254C0004')                           # current.pred=new
    out=len(q); q+=bytes.fromhex('285F265F245F2A1F281F261F4E75')

    m.patch(q,small,out); m.patch(q,at_end,ins); m.patch(q,before,ins); m.patch(q,again,loop)
    m.patch(q,no_prev,head); m.patch(q,linked_prev,after_prev); m.patch(q,no_next,out)
    return bytes(q)


def replace_once(image, old, new, what):
    pos=image.find(old,8,0x0B00)
    if pos<0: raise ValueError(f'M2.19 could not locate {what}')
    if image.find(old,pos+1,0x0B00)>=0: raise ValueError(f'M2.19 ambiguous {what}')
    image[pos:pos+len(old)]=new


def build():
    image=bytearray(p.build())

    # Replace AddMemList implementation in its fixed slot.
    code=addmemlist_code_m219()
    if len(code)>m.BASE_AVAIL_OFF-m.ADDMEM_OFF:
        raise ValueError('M2.19 AddMemList exceeds fixed slot')
    image[m.ADDMEM_OFF:m.BASE_AVAIL_OFF]=b'\xff'*(m.BASE_AVAIL_OFF-m.ADDMEM_OFF)
    image[m.ADDMEM_OFF:m.ADDMEM_OFF+len(code)]=code

    # M2.17 originally qualified prepend order C->B->A. With priorities
    # A=5, B=3, C=7 the qualified order must be C->A->B.
    old1=bytes.fromhex('0CB9')+struct.pack('>II',m.BBASE,m.CBASE)
    new1=bytes.fromhex('0CB9')+struct.pack('>II',m.ABASE,m.CBASE)
    old2=bytes.fromhex('0CB9')+struct.pack('>II',m.ABASE,m.BBASE)
    new2=bytes.fromhex('0CB9')+struct.pack('>II',m.BBASE,m.ABASE)
    replace_once(image,old1,new1,'C successor assertion')
    replace_once(image,old2,new2,'A successor assertion')

    # Chain an M2.19-specific topology gate after M2.18's final green path.
    boot=image[8:0x0B00]
    sig=bytes.fromhex('33FC00F000DFF1806000')
    gp=boot.rfind(sig)
    if gp<0: raise ValueError('M2.18 final success gate not found')
    good_abs=8+gp; branch_pos=good_abs+8
    fail_sig=bytes.fromhex('33FC000F00DFF18060FE')
    fp=boot.find(fail_sig,gp)
    if fp<0: raise ValueError('M2.18 final fail gate not found')
    test_abs=8+fp+len(fail_sig)

    c=bytearray(); fails=[]
    # Head C(pri 7), then A(pri 5), then B(pri 3), with consistent pred links.
    for value,address in (
        (m.CBASE,m.DYN_HEAD),
        (m.ABASE,m.CBASE+0),(0,m.CBASE+4),
        (m.BBASE,m.ABASE+0),(m.CBASE,m.ABASE+4),
        (0,m.BBASE+0),(m.ABASE,m.BBASE+4),
    ):
        fails.append(m.cmpabs(c,value,address))
    c+=m.mw(0x00f0,m.COLOR00); ok=m.branch(c,0x6000)
    bad=len(c); c+=m.mw(0x000f,m.COLOR00); idle=len(c); c+=bytes.fromhex('60FE')
    for x in fails: m.patch(c,x,bad)
    m.patch(c,ok,idle)
    if test_abs+len(c)>=0x0B00: raise ValueError('M2.19 runtime probe exceeds bootstrap area')
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
    if len(sys.argv)!=2: raise SystemExit('usage: make_m2_19_rom.py OUTPUT')
    out=Path(sys.argv[1]); data=build(); out.write_bytes(data)
    print(f'M2.19 ROM built: {out} ({len(data)} bytes)')
