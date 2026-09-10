#!/usr/bin/env python3
from pathlib import Path
import struct, sys

ROM_SIZE=512*1024; SP=0x0007FFFC; PC=0x00F80008; EXEC_BASE=0x00003400
MEMHDR=0x00004800; MEM_BASE=0x00005000; MEM_SIZE=0x1000
MARKER_OFF=0x1600; IDENT_OFF=0x1680
MARKER=b'LIBREKICK-M2.7\0EXEC-MEMHEADER-MEMCHUNK\0'
IDENT=b'exec.library\0LibreKick M2.7 MemHeader/MemChunk allocator slice 40.7\0'

def ones(t,v): t+=v; return (t&0xffffffff)+(t>>32)
if len(sys.argv)!=2: raise SystemExit('usage: check_m2_7.py ROM')
p=Path(sys.argv[1]); data=p.read_bytes()
assert len(data)==ROM_SIZE, f'wrong ROM size {len(data)}'
assert struct.unpack_from('>II',data,0)==(SP,PC), 'bad reset vectors'
assert data[MARKER_OFF:MARKER_OFF+len(MARKER)]==MARKER, 'missing M2.7 marker'
assert data[IDENT_OFF:IDENT_OFF+len(IDENT)]==IDENT, 'missing M2.7 identity'
boot=data[8:0x0B00]
assert bytes.fromhex('13FC000300BFE201') in boot, 'missing CIAA setup'
assert bytes.fromhex('08B9000000BFE001') in boot, 'missing OVL clear'
assert bytes.fromhex('23FC0000340000000004') in boot, 'SysBase != $3400'
assert bytes.fromhex('33FC00D800003410') in boot, 'lib_NegSize != 216'
assert bytes.fromhex('33FC002800003414') in boot, 'lib_Version != 40'
assert bytes.fromhex('33FC000700003416') in boot, 'lib_Revision != 7'
for lvo,off in ((198,0x0B00),(210,0x0C00),(216,0x0D00)):
    slot=EXEC_BASE-lvo; target=0x00F80000+off
    assert struct.pack('>I',slot) in boot, f'missing LVO -{lvo} slot'
    assert struct.pack('>H',target&0xffff) in boot, f'missing LVO -{lvo} target'
# MemHeader canonical subset and initial MemChunk.
assert struct.pack('>I',MEM_BASE) in boot, 'missing MemHeader first/lower'
assert struct.pack('>I',MEM_BASE+MEM_SIZE) in boot, 'missing MemHeader upper'
assert struct.pack('>I',MEM_SIZE) in boot, 'missing free-size initialization'
assert boot.count(bytes.fromhex('4EAEFF3A'))==3, 'expected three AllocMem calls'
assert boot.count(bytes.fromhex('4EAEFF2E'))==3, 'expected three FreeMem calls'
assert boot.count(bytes.fromhex('4EAEFF28'))==4, 'expected four AvailMem calls'
assert bytes.fromhex('0680000000070280FFFFFFF8') in data[0x0B00:0x0D00], 'missing 8-byte alignment path'
assert bytes.fromhex('33FC00F000DFF180') in boot, 'missing green PASS marker'
assert bytes.fromhex('33FC000F00DFF180') in boot, 'missing blue FAIL marker'
# Guard the Bcc.W PC-base regression fixed in M2.5.
probe=bytearray(b'\x67\x00\x00\x00'); pos=0; target=10
struct.pack_into('>h',probe,2,target-(pos+2))
assert struct.unpack_from('>h',probe,2)[0]==8
# No address-register TST encodings in allocator area.
assert bytes.fromhex('4A89') not in data[0x0B00:0x0D10], 'illegal TST.L A1 regression'
assert bytes.fromhex('4A8A') not in data[0x0B00:0x0D10], 'illegal TST.L A2 regression'
t=0
for o in range(0,ROM_SIZE,4): t=ones(t,struct.unpack_from('>I',data,o)[0])
t=(t&0xffffffff)+(t>>32); assert t==0xffffffff, f'bad checksum {t:08x}'
print(f'M2.7 check PASS: {p} ({len(data)} bytes)')
print('Exec AllocMem/FreeMem/AvailMem; one-region MemHeader/MemChunk split+coalesce slice; checksum=0xffffffff')
