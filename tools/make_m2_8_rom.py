#!/usr/bin/env python3
"""Build LibreKick M2.8: sorted MemChunk free-list + bidirectional coalescing.

M2.8 extends the single-region M2.7 allocator. FreeMem inserts by address,
keeps multiple free chunks, and coalesces with both successor and predecessor.
The runtime probe deliberately frees allocations out of order.
"""
from pathlib import Path
import struct, sys
from librekick_exec_abi import EXEC_BASE

ROM_SIZE=512*1024; ROM_BASE=0x00F80000; SP=0x0007FFFC; PC=ROM_BASE+8
COLOR00=0x00DFF180; CIAA_PRA=0x00BFE001; CIAA_DDRA=0x00BFE201
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
def patch(c,p,t): struct.pack_into('>h',c,p+2,t-(p+2))
def cmpd0(c,v): c+=bytes.fromhex('0C80')+struct.pack('>I',v); return branch(c,0x6600)
def cmpabs(c,v,a): c+=bytes.fromhex('0CB9')+struct.pack('>II',v,a); return branch(c,0x6600)
def ones(a,b): s=a+b; return (s&0xffffffff)+(s>>32)

def allocmem_code():
 q=bytearray(bytes.fromhex('2F012F022F032F082F092F0A2F0B'))
 q+=bytes.fromhex('4A80'); bad0=branch(q,0x6700); q+=bytes.fromhex('0680000000070280FFFFFFF8'); q+=bytes.fromhex('2200')
 q+=bytes.fromhex('2079')+struct.pack('>I',MEMHDR+MH_FIRST)+bytes.fromhex('267C00000000')
 loop=len(q); q+=bytes.fromhex('26084A83'); exhausted=branch(q,0x6700); q+=bytes.fromhex('24280004'); q+=bytes.fromhex('20029081'); too_small=branch(q,0x6500); q+=bytes.fromhex('0C8000000008'); whole=branch(q,0x6500)
 q+=bytes.fromhex('2448D5C1'); q+=bytes.fromhex('2490'); q+=bytes.fromhex('25400004'); q+=bytes.fromhex('220B4A81'); head=branch(q,0x6700); q+=bytes.fromhex('268A'); linked=branch(q,0x6000)
 h=len(q); q+=bytes.fromhex('23CA')+struct.pack('>I',MEMHDR+MH_FIRST); l=len(q); q+=bytes.fromhex('23C2')+struct.pack('>I',MEMHDR+MH_FREE)+bytes.fromhex('2008'); out=branch(q,0x6000)
 w=len(q); q+=bytes.fromhex('220B4A81'); wh=branch(q,0x6700); q+=bytes.fromhex('2690'); wl=branch(q,0x6000); whp=len(q); q+=bytes.fromhex('23D0')+struct.pack('>I',MEMHDR+MH_FIRST); wlp=len(q); q+=bytes.fromhex('23C3')+struct.pack('>I',MEMHDR+MH_FREE)+bytes.fromhex('2008'); wout=branch(q,0x6000)
 ts=len(q); q+=bytes.fromhex('2648'); q+=bytes.fromhex('2050'); again=branch(q,0x6000)
 fail=len(q); q+=bytes.fromhex('7000'); done=len(q); q+=bytes.fromhex('265F245F225F205F261F241F221F4E75')
 for p in (bad0,exhausted): patch(q,p,fail)
 patch(q,too_small,ts); patch(q,whole,w); patch(q,head,h); patch(q,linked,l); patch(q,out,done); patch(q,wh,whp); patch(q,wl,wlp); patch(q,wout,done); patch(q,again,loop)
 return bytes(q)

def freemem_code():
 q=bytearray(bytes.fromhex('2F012F022F032F082F0A2F0B')); q+=bytes.fromhex('22094A81'); r0=branch(q,0x6700); q+=bytes.fromhex('4A80'); r1=branch(q,0x6700); q+=bytes.fromhex('0680000000070280FFFFFFF8'); q+=bytes.fromhex('2400'); q+=bytes.fromhex('2079')+struct.pack('>I',MEMHDR+MH_FIRST)+bytes.fromhex('267C00000000')
 loop=len(q); q+=bytes.fromhex('22084A81'); ie=branch(q,0x6700); q+=bytes.fromhex('2609B283'); ib=branch(q,0x6200); q+=bytes.fromhex('26482050'); ag=branch(q,0x6000)
 ins=len(q); q+=bytes.fromhex('2288'); q+=bytes.fromhex('23420004'); q+=bytes.fromhex('220B4A81'); ah=branch(q,0x6700); q+=bytes.fromhex('2689'); lk=branch(q,0x6000); hp=len(q); q+=bytes.fromhex('23C9')+struct.pack('>I',MEMHDR+MH_FIRST); lkp=len(q); q+=bytes.fromhex('2239')+struct.pack('>I',MEMHDR+MH_FREE)+bytes.fromhex('D28223C1')+struct.pack('>I',MEMHDR+MH_FREE)
 q+=bytes.fromhex('22084A81'); nn=branch(q,0x6700); q+=bytes.fromhex('2449D5C2'); q+=bytes.fromhex('220A2608B283'); nn2=branch(q,0x6600); q+=bytes.fromhex('22280004D3A90004'); q+=bytes.fromhex('2450228A'); nnp=len(q)
 q+=bytes.fromhex('220B4A81'); np=branch(q,0x6700); q+=bytes.fromhex('244B222B0004D5C1'); q+=bytes.fromhex('220A2609B283'); np2=branch(q,0x6600); q+=bytes.fromhex('22290004D3AB0004'); q+=bytes.fromhex('2451268A'); npp=len(q); out=len(q); q+=bytes.fromhex('265F245F205F261F241F221F4E75')
 patch(q,r0,out); patch(q,r1,out); patch(q,ie,ins); patch(q,ib,ins); patch(q,ag,loop); patch(q,ah,hp); patch(q,lk,lkp); patch(q,nn,nnp); patch(q,nn2,nnp); patch(q,np,npp); patch(q,np2,npp); return bytes(q)

def availmem_code(): return bytes.fromhex('2039')+struct.pack('>I',MEMHDR+MH_FREE)+bytes.fromhex('4E75')

def build():
 image=bytearray([0xff])*ROM_SIZE; struct.pack_into('>II',image,0,SP,PC); c=bytearray(bytes.fromhex('46FC2700'))
 c+=mb(3,CIAA_DDRA)+bclr0(CIAA_PRA)+ml(EXEC_BASE,4)+ml(0,EXEC_BASE)+ml(0,EXEC_BASE+4)+mw(0x0900,EXEC_BASE+8)+ml(IDSTRING_ADDR,EXEC_BASE+10)+mw(0,EXEC_BASE+14)+mw(216,EXEC_BASE+16)+mw(34,EXEC_BASE+18)+mw(40,EXEC_BASE+20)+mw(8,EXEC_BASE+22)+ml(IDSTRING_ADDR,EXEC_BASE+24)+ml(0,EXEC_BASE+28)+mw(0,EXEC_BASE+32)
 for off,t in FUNCS.items(): c+=vector(t,EXEC_BASE-off)
 c+=mw(MEMF_CHIP,MEMHDR+MH_ATTR)+ml(MEM_BASE,MEMHDR+MH_FIRST)+ml(MEM_BASE,MEMHDR+MH_LOWER)+ml(MEM_BASE+MEM_SIZE,MEMHDR+MH_UPPER)+ml(MEM_SIZE,MEMHDR+MH_FREE)+ml(0,MEM_BASE)+ml(MEM_SIZE,MEM_BASE+4)+mw(0x0f00,COLOR00)+b'\x4d\xf9'+struct.pack('>I',EXEC_BASE)
 fails=[]
 def alloc(n,e):
  nonlocal c; c+=bytes.fromhex('203C')+struct.pack('>I',n)+bytes.fromhex('223C00000002')+bytes.fromhex('4EAEFF3A'); fails.append(cmpd0(c,e))
 def free(a,n):
  nonlocal c; c+=bytes.fromhex('227C')+struct.pack('>I',a)+bytes.fromhex('203C')+struct.pack('>I',n)+bytes.fromhex('4EAEFF2E')
 alloc(0x100,MEM_BASE); alloc(0x180,MEM_BASE+0x100); alloc(0x80,MEM_BASE+0x280); free(MEM_BASE+0x100,0x180); free(MEM_BASE,0x100); free(MEM_BASE+0x280,0x80)
 fails += [cmpabs(c,MEM_BASE,MEMHDR+MH_FIRST),cmpabs(c,0,MEM_BASE),cmpabs(c,MEM_SIZE,MEM_BASE+4),cmpabs(c,MEM_SIZE,MEMHDR+MH_FREE)]
 c+=bytes.fromhex('223C00080000')+bytes.fromhex('4EAEFF28'); fails.append(cmpd0(c,MEM_SIZE)); c+=mw(0x00f0,COLOR00); ok=branch(c,0x6000); bad=len(c); c+=mw(0x000f,COLOR00); idle=len(c); c+=bytes.fromhex('60FE')
 for p in fails: patch(c,p,bad)
 patch(c,ok,idle); image[8:8+len(c)]=c; image[0x0B00:0x0B00+len(allocmem_code())]=allocmem_code(); image[0x0C00:0x0C00+len(freemem_code())]=freemem_code(); image[0x0D00:0x0D00+len(availmem_code())]=availmem_code(); marker=b'LIBREKICK-M2.8\0EXEC-MEM-FREELIST\0'; ident=b'exec.library\0LibreKick M2.8 free-list slice 40.8\0'; image[MARKER_OFF:MARKER_OFF+len(marker)]=marker; image[IDENT_OFF:IDENT_OFF+len(ident)]=ident
 struct.pack_into('>I',image,ROM_SIZE-4,0); total=0
 for o in range(0,ROM_SIZE-4,4): total=ones(total,struct.unpack_from('>I',image,o)[0])
 total=(total&0xffffffff)+(total>>32); struct.pack_into('>I',image,ROM_SIZE-4,(~total)&0xffffffff); return image
if __name__=='__main__':
 if len(sys.argv)!=2: raise SystemExit('usage: make_m2_8_rom.py OUTPUT')
 out=Path(sys.argv[1]); data=build(); out.write_bytes(data); print(f'M2.8 ROM built: {out} ({len(data)} bytes)')
