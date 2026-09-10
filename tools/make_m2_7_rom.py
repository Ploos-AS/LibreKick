#!/usr/bin/env python3
"""Build LibreKick M2.7: first MemHeader/MemChunk-based Exec allocator slice.

Scope: one 4 KiB CHIP memory region, 8-byte alignment, first-fit splitting,
sorted FreeMem reinsertion with adjacent coalescing, and AvailMem(MEMF_TOTAL).
"""
from pathlib import Path
import struct, sys

ROM_SIZE=512*1024; ROM_BASE=0x00F80000; SP=0x0007FFFC; PC=ROM_BASE+8
EXEC_BASE=0x00003400; COLOR00=0x00DFF180; CIAA_PRA=0x00BFE001; CIAA_DDRA=0x00BFE201
MEMHDR=0x00004800; MEM_BASE=0x00005000; MEM_SIZE=0x1000
# MemHeader subset at canonical offsets after struct Node (14 bytes):
MH_ATTR=14; MH_FIRST=16; MH_LOWER=20; MH_UPPER=24; MH_FREE=28
MARKER_OFF=0x1600; IDENT_OFF=0x1680; IDSTRING_ADDR=ROM_BASE+IDENT_OFF
FUNCS={198:ROM_BASE+0x0B00,210:ROM_BASE+0x0C00,216:ROM_BASE+0x0D00}
MEMF_CHIP=0x0002; MEMF_TOTAL=0x00080000

def ml(v,a): return b'\x23\xfc'+struct.pack('>II',v,a)
def mw(v,a): return b'\x33\xfc'+struct.pack('>H',v)+struct.pack('>I',a)
def mb(v,a): return b'\x13\xfc'+struct.pack('>H',v&0xff)+struct.pack('>I',a)
def bclr0(a): return bytes.fromhex('08B90000')+struct.pack('>I',a)
def vector(t,a): return ml(0x4EF90000|((t>>16)&0xffff),a)+mw(t&0xffff,a+4)
def branch(c,op): p=len(c); c+=struct.pack('>HH',op,0); return p
def patch(c,p,t):
    # 68000 Bcc.W displacement is relative to opcode address + 2.
    d=t-(p+2)
    if not -32768<=d<=32767: raise ValueError('branch displacement')
    struct.pack_into('>h',c,p+2,d)
def cmpd0(c,v): c+=bytes.fromhex('0C80')+struct.pack('>I',v); return branch(c,0x6600)
def cmpabs(c,v,a): c+=bytes.fromhex('0CB9')+struct.pack('>II',v,a); return branch(c,0x6600)
def ones(t,v): t+=v; return (t&0xffffffff)+(t>>32)

def allocmem_code():
    # D0=size, D1=requirements -> D0=memory or NULL.
    # Internal registers are saved; first-fit over MemChunk {next,bytes}.
    q=bytearray(bytes.fromhex('2F012F082F092F0A2F0B'))       # d1/a0-a3
    q+=bytes.fromhex('4A80'); z=branch(q,0x6700)             # zero size -> fail
    q+=bytes.fromhex('0680000000070280FFFFFFF8')           # align D0 to 8
    q+=bytes.fromhex('2A00')                                 # d5 unavailable! avoid
    # Use d1 as requested size after saving original requirements.
    q+=bytes.fromhex('2200')                                 # move.l d0,d1
    q+=bytes.fromhex('207900004810')                         # a0 = mh_First (abs.l)
    q+=bytes.fromhex('267C00000000')                         # a3 = prev=NULL
    loop=len(q)
    q+=bytes.fromhex('20084A80'); fail=branch(q,0x6700)      # a0==NULL
    q+=bytes.fromhex('24280004')                             # d2 = chunk bytes
    q+=bytes.fromhex('B481'); small=branch(q,0x6500)         # d2 < d1 => next
    # remaining = d2-d1 in d2. If >=8, split at chunk+d1.
    q+=bytes.fromhex('9481')                                 # sub.l d1,d2
    q+=bytes.fromhex('0C8200000008'); whole=branch(q,0x6500) # remainder <8 => whole
    q+=bytes.fromhex('2448D5C1')                             # a2=a0; adda.l d1,a2
    q+=bytes.fromhex('24A80000')                             # (a2)=chunk->next
    q+=bytes.fromhex('25420004')                             # 4(a2)=remainder
    q+=bytes.fromhex('200B4A80'); headsplit=branch(q,0x6700)
    q+=bytes.fromhex('274A0000'); splitlinked=branch(q,0x6000) # prev->next=a2
    hs=len(q); q+=bytes.fromhex('23CA00004810')               # mh_First=a2
    sl=len(q)
    q+=bytes.fromhex('20390000481C9280')                     # d0=mh_Free; sub req
    q+=bytes.fromhex('23C00000481C')                         # mh_Free=d0
    q+=bytes.fromhex('2008'); done=branch(q,0x6000)          # return original chunk
    # whole chunk: unlink from list and charge full chunk bytes.
    wh=len(q)
    q+=bytes.fromhex('2450')                                 # a2=chunk->next
    q+=bytes.fromhex('200B4A80'); headwhole=branch(q,0x6700)
    q+=bytes.fromhex('274A0000'); wholelinked=branch(q,0x6000)
    hwh=len(q); q+=bytes.fromhex('23CA00004810')
    wl=len(q)
    q+=bytes.fromhex('20390000481C9428')+bytes.fromhex('0004') # d0=free; sub 4(a0)
    q+=bytes.fromhex('23C00000481C2008'); whdone=branch(q,0x6000)
    nxt=len(q); q+=bytes.fromhex('26482050'); again=branch(q,0x6000) # prev=a0; a0=(a0)
    bad=len(q); q+=bytes.fromhex('7000')
    out=len(q); q+=bytes.fromhex('265F245F225F205F221F4E75')
    patch(q,z,bad); patch(q,fail,bad); patch(q,small,nxt); patch(q,whole,wh)
    patch(q,headsplit,hs); patch(q,splitlinked,sl); patch(q,done,out)
    patch(q,headwhole,hwh); patch(q,wholelinked,wl); patch(q,whdone,out); patch(q,again,loop)
    return bytes(q)

def freemem_code():
    # A1=block, D0=size. Reinsert sorted; coalesce with next and previous.
    # M2.7 qualification frees a previously allocated exact block.
    q=bytearray(bytes.fromhex('2F002F012F082F092F0A2F0B'))
    q+=bytes.fromhex('4A894A80')                             # a1? then size?
    # Explicit null/zero checks using data register for 68000 legality.
    q+=bytes.fromhex('22094A81'); ret0=branch(q,0x6700)
    q+=bytes.fromhex('4A80'); ret1=branch(q,0x6700)
    q+=bytes.fromhex('0680000000070280FFFFFFF8')           # align size
    q+=bytes.fromhex('2400')                                 # d2=size
    q+=bytes.fromhex('207900004810')                         # a0=head
    q+=bytes.fromhex('267C00000000')                         # a3=prev NULL
    loop=len(q)
    q+=bytes.fromhex('20084A80'); ins=branch(q,0x6700)
    q+=bytes.fromhex('B3C8'); ins_before=branch(q,0x6500)     # cmpa.l a0,a1; a1<=a0
    q+=bytes.fromhex('26482050'); again=branch(q,0x6000)
    insert=len(q)
    # a1->next=a0; a1->bytes=d2; link prev/head
    q+=bytes.fromhex('228822420004')
    q+=bytes.fromhex('200B4A80'); athead=branch(q,0x6700)
    q+=bytes.fromhex('27490000'); linked=branch(q,0x6000)
    ah=len(q); q+=bytes.fromhex('23C900004810')
    lk=len(q)
    # mh_Free += d2
    q+=bytes.fromhex('20390000481CD08223C00000481C')
    # Coalesce with next if end(this)==next.
    q+=bytes.fromhex('2449D5C2')                             # a2=a1+size
    q+=bytes.fromhex('2051')                                 # a0=(a1) next
    q+=bytes.fromhex('20084A80'); skipnext=branch(q,0x6700)
    q+=bytes.fromhex('B5C8'); skipnext2=branch(q,0x6600)      # cmpa.l a0,a2
    q+=bytes.fromhex('24110082')                             # d2? placeholder avoided below
    # overwrite previous four bytes with move.l 4(a0),d1 + add to 4(a1), and next link
    q[-4:]=bytes.fromhex('22280004')                         # d1=next->bytes
    q+=bytes.fromhex('D3A90004')                             # add.l d1,4(a1)
    q+=bytes.fromhex('22900000')                             # a1->next = next->next
    sn=len(q)
    # Coalesce previous if prev != NULL and prev+prevbytes == a1.
    q+=bytes.fromhex('200B4A80'); skipprev=branch(q,0x6700)
    q+=bytes.fromhex('244B242A0004D5C2')                    # a2=prev; d2=prevbytes; a2+=d2
    q+=bytes.fromhex('B5C9'); skipprev2=branch(q,0x6600)
    q+=bytes.fromhex('22290004D3AB0004')                    # d1=this bytes; add to prev bytes
    q+=bytes.fromhex('26910000')                             # prev->next=this->next
    sp=len(q)
    out=len(q); q+=bytes.fromhex('265F245F225F205F221F201F4E75')
    patch(q,ret0,out); patch(q,ret1,out); patch(q,ins,insert); patch(q,ins_before,insert); patch(q,again,loop)
    patch(q,athead,ah); patch(q,linked,lk); patch(q,skipnext,sn); patch(q,skipnext2,sn)
    patch(q,skipprev,sp); patch(q,skipprev2,sp)
    return bytes(q)

def availmem_code():
    # D1 requirements. M2.7 implements total-free semantics for its one region.
    return bytes.fromhex('20390000481C4E75')

def build():
    image=bytearray([0xff])*ROM_SIZE; struct.pack_into('>II',image,0,SP,PC)
    c=bytearray(bytes.fromhex('46FC2700')); c+=mb(3,CIAA_DDRA); c+=bclr0(CIAA_PRA); c+=ml(EXEC_BASE,4)
    c+=ml(0,EXEC_BASE)+ml(0,EXEC_BASE+4)+mw(0x0900,EXEC_BASE+8)+ml(IDSTRING_ADDR,EXEC_BASE+10)
    c+=mw(0,EXEC_BASE+14)+mw(216,EXEC_BASE+16)+mw(34,EXEC_BASE+18)+mw(40,EXEC_BASE+20)+mw(7,EXEC_BASE+22)+ml(IDSTRING_ADDR,EXEC_BASE+24)+ml(0,EXEC_BASE+28)+mw(0,EXEC_BASE+32)
    for off,t in FUNCS.items(): c+=vector(t,EXEC_BASE-off)
    # MemHeader subset + one initial MemChunk covering 4 KiB.
    c+=mw(MEMF_CHIP,MEMHDR+MH_ATTR)+ml(MEM_BASE,MEMHDR+MH_FIRST)+ml(MEM_BASE,MEMHDR+MH_LOWER)+ml(MEM_BASE+MEM_SIZE,MEMHDR+MH_UPPER)+ml(MEM_SIZE,MEMHDR+MH_FREE)
    c+=ml(0,MEM_BASE)+ml(MEM_SIZE,MEM_BASE+4)
    c+=mw(0x0f00,COLOR00)+b'\x4d\xf9'+struct.pack('>I',EXEC_BASE)
    fails=[]
    # Initial AvailMem == 4096.
    c+=bytes.fromhex('223C000800004EAEFF28'); fails.append(cmpd0(c,MEM_SIZE))
    # Alloc 0x100 -> MEM_BASE; free drops to 0xF00.
    c+=bytes.fromhex('70000100223C000000024EAEFF3A'); fails.append(cmpd0(c,MEM_BASE))
    c+=bytes.fromhex('223C000800004EAEFF28'); fails.append(cmpd0(c,MEM_SIZE-0x100))
    # Alloc 0x80 -> MEM_BASE+0x100; splitting advances head.
    c+=bytes.fromhex('70000080223C000000024EAEFF3A'); fails.append(cmpd0(c,MEM_BASE+0x100))
    fails.append(cmpabs(c,MEM_BASE+0x180,MEMHDR+MH_FIRST))
    # Free first 0x100, then allocate 0x40 and require first-fit reuse/split.
    c+=bytes.fromhex('227C')+struct.pack('>I',MEM_BASE)+bytes.fromhex('700001004EAEFF2E')
    c+=bytes.fromhex('70000040223C000000024EAEFF3A'); fails.append(cmpd0(c,MEM_BASE))
    # Free 0x40 and 0x80. Coalescing must restore one 4 KiB chunk.
    c+=bytes.fromhex('227C')+struct.pack('>I',MEM_BASE)+bytes.fromhex('700000404EAEFF2E')
    c+=bytes.fromhex('227C')+struct.pack('>I',MEM_BASE+0x100)+bytes.fromhex('700000804EAEFF2E')
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
    marker=b'LIBREKICK-M2.7\0EXEC-MEMHEADER-MEMCHUNK\0'; ident=b'exec.library\0LibreKick M2.7 MemHeader/MemChunk allocator slice 40.7\0'
    image[MARKER_OFF:MARKER_OFF+len(marker)]=marker; image[IDENT_OFF:IDENT_OFF+len(ident)]=ident
    struct.pack_into('>I',image,ROM_SIZE-4,0); total=0
    for o in range(0,ROM_SIZE-4,4): total=ones(total,struct.unpack_from('>I',image,o)[0])
    total=(total&0xffffffff)+(total>>32); struct.pack_into('>I',image,ROM_SIZE-4,(~total)&0xffffffff)
    return image

if __name__=='__main__':
    if len(sys.argv)!=2: raise SystemExit('usage: make_m2_7_rom.py OUTPUT')
    out=Path(sys.argv[1]); data=build(); out.write_bytes(data); print(f'M2.7 ROM built: {out} ({len(data)} bytes)')
