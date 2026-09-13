#!/usr/bin/env python3
from pathlib import Path
import struct,sys
p=Path(sys.argv[1]); data=p.read_bytes()
assert len(data)==512*1024
assert struct.unpack_from('>II',data,0)==(0x0007FFFC,0x00F80008)
assert b'LIBREKICK-M2.20\0EXEC-ALLOCMEM-NOFLAG-SEMANTICS\0' in data
assert b'exec.library\0LibreKick M2.20 AllocMem no-region semantics slice 40.20\0' in data
alloc=data[0x0B00:0x0C00]
# No-region path must call FAST allocator before CHIP allocator.
fast_call=bytes.fromhex('4EB9')+struct.pack('>I',0x00F80000+0x1000)
chip_call=bytes.fromhex('4EB9')+struct.pack('>I',0x00F80000+0x0E00)
assert fast_call in alloc and chip_call in alloc
assert alloc.find(fast_call) < alloc.find(chip_call), 'no-region path does not prefer FAST'
# Dynamic linked traversal remains present.
assert struct.pack('>I',0x4C00) in alloc
assert bytes.fromhex('2050') in alloc
# Regression guards: D5 is the invariant dynamic-region mode. It must be
# copied to D1 with MOVE.L, not MOVE.W, because D1 originally contains the
# full requirements mask and upper bits such as MEMF_CLEAR would survive a
# word-sized copy. D4 is separately zeroed before loading mh_Attributes.w.
assert bytes.fromhex('7A00') in alloc, 'missing no-region D5 mode'
assert bytes.fromhex('7A02') in alloc, 'missing CHIP D5 mode'
assert bytes.fromhex('7A04') in alloc, 'missing FAST D5 mode'
assert bytes.fromhex('4A85') in alloc, 'dynamic any-mode test is not using D5'
assert bytes.fromhex('220578003828000E') in alloc, 'dynamic mode/attributes are not normalized before long comparison'
assert bytes.fromhex('320578003828000E') not in alloc, 'unsafe MOVE.W D5,D1 leaves stale requirements bits in D1'
# Runtime probe carries no-region requests (D1=0), CHIP|FAST rejection, a
# green success marker and the standard blue failure gate.
boot=data[8:0x0B00]
assert bytes.fromhex('223C00000000') in boot
assert bytes.fromhex('223C00000006') in boot
assert bytes.fromhex('33FC00F000DFF180') in boot
assert bytes.fromhex('33FC000F00DFF18060FE') in boot
def ones(t,v):
    t+=v
    return (t&0xffffffff)+(t>>32)
t=0
for o in range(0,len(data),4): t=ones(t,struct.unpack_from('>I',data,o)[0])
t=(t&0xffffffff)+(t>>32)
assert t==0xffffffff, f'bad checksum {t:08x}'
print(f'M2.20 check PASS: {p} ({len(data)} bytes)')
print('Exec AllocMem no-region FAST preference + CHIP/dynamic fallback; checksum=0xffffffff')