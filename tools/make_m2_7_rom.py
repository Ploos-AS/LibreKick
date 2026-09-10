#!/usr/bin/env python3
"""Build LibreKick M2.7: first MemHeader/MemChunk-based Exec allocator slice.

M2.7 intentionally qualifies one CHIP region with one active first-fit free chunk,
8-byte alignment, front splitting, LIFO reinsertion, adjacent-next coalescing and
AvailMem total-free accounting. Arbitrary sorted multi-chunk frees are deferred.
"""
from pathlib import Path
import struct, sys

ROM_SIZE=512*1024; ROM_BASE=0x00F80000; SP=0x0007FFFC; PC=ROM_BASE+8
EXEC_BASE=0x00003400; COLOR00=0x00DFF180; CIAA_PRA=0x00BFE001; CIAA_DDRA=0x00BFE201
MEMHDR=0x00004800; MEM_BASE=0x00005000; MEM_SIZE=0x1000
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
    d=t-(p+2)
    if not -32768<=d<=32767: raise ValueError('branch displacement')
    struct.pack_into('>h',c,p+2,d)
def cmpd0(c,v): c+=bytes.fromhex('0C80')+struct.pack('>I',v); return branch(c,0x6600)
def cmpabs(c,v,a): c+=bytes.fromhex('0CB9')+struct.pack('>II',v,a); return branch(c,0x6600)
def ones(t,v): t+=v; return (t&0xffffffff)+(t>>32)

def allocmem_code():
    # D0=size, D1=requirements -> D0=memory or NULL.
    q=bytearray(bytes.fromhex('2F012F022F082F092F0A'))       # save d1,d2,a0,a1,a2
    q+=bytes.fromhex('4A80'); bad0=branch(q,0x6700)
    q+=bytes.fromhex('0680000000070280FFFFFFF8')           # align size to 8
    q+=bytes.fromhex('2200')                                 # d1=requested size
    q+=bytes.fromhex('207900004810')                         # a0=mh_First
    q+=bytes.fromhex('20084A80'); bad1=branch(q,0x6700)
    q+=bytes.fromhex('24280004')                             # d2=chunk bytes
    q+=bytes.fromhex('20029081'); too_big=branch(q,0x6500)   # d0=d2-d1; borrow => fail
    q+=bytes.fromhex('0C8000000008'); whole=branch(q,0x6500) # remainder < 8 => whole chunk
    # Split first free chunk: new chunk begins at old + requested.
    q+=bytes.fromhex('2448D5C1')                             # a2=a0; a2+=d1
    q+=bytes.fromhex('2490')                                 # (a2)=(a0) next
    q+=bytes.fromhex('25400004')                             # 4(a2)=remainder d0
    q+=bytes.fromhex('23CA00004810')                         # mh_First=a2
    q+=bytes.fromhex('24390000481C948123C20000481C')       # mh_Free -= d1
    q+=bytes.fromhex('2008'); done_split=branch(q,0x6000)
    # Whole chunk path: unlink head and account its complete size.
    wh=len(q)
    q+=bytes.fromhex('2450')                                 # a2=(a0)
    q+=bytes.fromhex('23CA00004810')                         # mh_First=a2
    q+=bytes.fromhex('20390000481C908223C00000481C')       # mh_Free -= d2
    q+=bytes.fromhex('2008'); done_whole=branch(q,0x6000)
    bad=len(q); q+=bytes.fromhex('7000')
    out=len(q); q+=bytes.fromhex('245F225F205F241F221F4E75')
    for p in (bad0,bad1,too_big): patch(q,p,bad)
    patch(q,whole,wh); patch(q,done_split,out); patch(q,done_whole,out)
    return bytes(q)

def freemem_code():
    # A1=block, D0=size. M2.7 reinserts at head and coalesces with adjacent head.
    q=bytearray(bytes.fromhex('2F012F022F082F0A'))           # save d1,d2,a0,a2
    q+=bytes.fromhex('22094A81'); ret0=branch(q,0x6700)      # NULL block
    q+=bytes.fromhex('4A80'); ret1=branch(q,0x6700)          # zero size
    q+=bytes.fromhex('0680000000070280FFFFFFF8')           # align size
    q+=bytes.fromhex('2400')                                 # d2=size
    q+=bytes.fromhex('207900004810')                         # a0=old head
    q+=bytes.fromhex('2288')                                 # a1->next=a0
    q+=bytes.fromhex('23420004')                             # a1->bytes=d2
    q+=bytes.fromhex('23C900004810')                         # mh_First=a1
    q+=bytes.fromhex('22390000481CD28223C10000481C')       # mh_Free += d2
    # If this block ends exactly at old head, merge them.
    q+=bytes.fromhex('22084A81'); no_merge=branch(q,0x6700)
    q+=bytes.fromhex('2449D5C2')                             # a2=a1+d2
    q+=bytes.fromhex('200AB081'); no_merge2=branch(q,0x6600) # a2 != old head
    q+=bytes.fromhex('22280004D3A90004')                    # a1.bytes += old.bytes
    q+=bytes.fromhex('2450228A')                             # a1.next = old.next
    out=len(q); q+=bytes.fromhex('245F205F241F221F4E75')
    patch(q,ret0,out); patch(q,ret1,out); patch(q,no_merge,out); patch(q,no_merge2,out)
    return bytes(q)

def availmem_code():
    # D1 flags accepted; this slice exposes total free bytes for its single region.
    return bytes.fromhex('20390000481C4E75')

def build():
    image=bytearray([0xff])*ROM_SIZE; struct.pack_into('>II',image,0,SP,PC)
    c=bytearray(bytes.fromhex('46FC2700')); c+=mb(3,CIAA_DDRA); c+=bclr0(CIAA_PRA); c+=ml(EXEC_BASE,4)
    c+=ml(0,EXEC_BASE)+ml(0,EXEC_BASE+4)+mw(0x0900,EXEC_BASE+8)+ml(IDSTRING_ADDR,EXEC_BASE+10)
    c+=mw(0,EXEC_BASE+14)+mw(216,EXEC_BASE+16)+mw(34,EXEC_BASE+18)+mw(40,EXEC_BASE+20)+mw(7,EXEC_BASE+22)+ml(IDSTRING_ADDR,EXEC_BASE+24)+ml(0,EXEC_BASE+28)+mw(0,EXEC_BASE+32)
    for off,t in FUNCS.items(): c+=vector(t,EXEC_BASE-off)
    # Canonical MemHeader field offsets and one initial MemChunk.
    c+=mw(MEMF_CHIP,MEMHDR+MH_ATTR)+ml(MEM_BASE,MEMHDR+MH_FIRST)+ml(MEM_BASE,MEMHDR+MH_LOWER)+ml(MEM_BASE+MEM_SIZE,MEMHDR+MH_UPPER)+ml(MEM_SIZE,MEMHDR+MH_FREE)
    c+=ml(0,MEM_BASE)+ml(MEM_SIZE,MEM_BASE+4)
    c+=mw(0x0f00,COLOR00)+b'\x4d\xf9'+struct.pack('>I',EXEC_BASE)
    fails=[]
    # Initial total free = 4096.
    c+=bytes.fromhex('223C000800004EAEFF28'); fails.append(cmpd0(c,MEM_SIZE))
    # Allocate 0x100 then 0x80; verify front splitting and accounting.
    c+=bytes.fromhex('203C00000100223C000000024EAEFF3A'); fails.append(cmpd0(c,MEM_BASE))
    c+=bytes.fromhex('223C000800004EAEFF28'); fails.append(cmpd0(c,MEM_SIZE-0x100))
    c+=bytes.fromhex('203C00000080223C000000024EAEFF3A'); fails.append(cmpd0(c,MEM_BASE+0x100))
    fails.append(cmpabs(c,MEM_BASE+0x180,MEMHDR+MH_FIRST))
    # Reverse-order frees exercise head reinsertion + adjacent coalescing.
    c+=bytes.fromhex('227C')+struct.pack('>I',MEM_BASE+0x100)+bytes.fromhex('203C000000804EAEFF2E')
    fails.append(cmpabs(c,MEM_BASE+0x100,MEMHDR+MH_FIRST))
    c+=bytes.fromhex('227C')+struct.pack('>I',MEM_BASE)+bytes.fromhex('203C000001004EAEFF2E')
    c+=bytes.fromhex('223C000800004EAEFF28'); fails.append(cmpd0(c,MEM_SIZE))
    fails.append(cmpabs(c,MEM_BASE,MEMHDR+MH_FIRST)); fails.append(cmpabs(c,0,MEM_BASE)); fails.append(cmpabs(c,MEM_SIZE,MEM_BASE+4))
    # Reuse after complete coalesce.
    c+=bytes.fromhex('203C00000040223C000000024EAEFF3A'); fails.append(cmpd0(c,MEM_BASE))
    c+=bytes.fromhex('227C')+struct.pack('>I',MEM_BASE)+bytes.fromhex('203C000000404EAEFF2E')
    c+=bytes.fromhex('223C000800004EAEFF28'); fails.append(cmpd0(c,MEM_SIZE))
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
