# M2.12 Exec AvailMem / MEMF_LARGEST Qualification

Status: **STATIC READY / RUNTIME PENDING**

M2.12 extends the M2.11 two-region memory model with more complete `AvailMem()` semantics. In particular, `MEMF_LARGEST` returns the size of the largest single free block matching the requested memory attributes rather than total free bytes.

Public Exec surface remains:

- `AllocMem()` at **-198(a6)**;
- `FreeMem()` at **-210(a6)**;
- `AvailMem()` at **-216(a6)**.

## Qualified scope

M2.12 adds:

- `AvailMem(MEMF_LARGEST)` across all matching regions;
- `AvailMem(MEMF_CHIP|MEMF_LARGEST)`;
- `AvailMem(MEMF_FAST|MEMF_LARGEST)`;
- largest-block traversal across fragmented `MemChunk` free lists;
- distinction between total free bytes and largest free block;
- maximum selection across CHIP and FAST regions when no region bit is supplied;
- rejection of conflicting CHIP|FAST requirements for largest-block queries;
- retained M2.11 CHIP/FAST total-free accounting and routing.

The A500 remains the 68000 runtime baseline. The FAST region is still a logical test region in ordinary addressable RAM and does not claim physical A500 Fast RAM.

## Runtime semantic probe

The ROM starts with two 4096-byte logical regions and verifies that combined `MEMF_LARGEST` initially returns 4096, not 8192.

It then deliberately fragments CHIP memory:

1. allocate A=`$5000/$100`, B=`$5100/$200`, C=`$5300/$100`;
2. free A and C;
3. CHIP free-list becomes `$5000/$100 -> $5300/$D00`;
4. CHIP total free must be `$E00` while CHIP largest must be `$D00`;
5. combined total free is `$1E00`, while combined largest remains `$1000` because FAST is still intact.

The probe then allocates `$400` from FAST:

- FAST total/largest become `$C00`;
- combined largest becomes CHIP's `$D00`;
- combined total becomes `$1A00`;
- CHIP|FAST|LARGEST must return zero because no region satisfies both requirements.

Finally all allocations are freed and both regions must return to one 4096-byte chunk each. Combined total returns to 8192 and combined largest returns to 4096.

Diagnostic colours: red = running, blue = semantic failure, green = complete PASS.

## Static gate

```sh
make clean
make check
```

The checker verifies the M2.12 identity/header, public memory LVOs, both logical region setups, the `MEMF_LARGEST` bit test, calls to distinct CHIP/FAST largest scanners, traversal of `mc_Next`, comparison of `mc_Bytes`, runtime constants distinguishing total from largest, PASS/FAIL markers, 68000 regression guards and final ROM checksum.

## Runtime gate

```sh
make qualify-m2_12
```

Target: FS-UAE A500 / 68000. Runtime PASS requires a stable green screen and normal manual emulator exit.

## Non-claims

M2.12 does not yet implement dynamically registered memory regions, `AddMemList()`, physical Fast RAM discovery, full region priority/ranking, or every historical Exec memory attribute. `AllocMem()` default region preference is unchanged from M2.11 and will be handled separately from this AvailMem-focused slice.

## Runtime record

- Date: pending
- Host: pending
- FS-UAE: pending
- CPU/model: A500 / 68000
- ROM identifier/hash: pending
- Diagnostic screen: pending
- Result: **PENDING**
