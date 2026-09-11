# M2.10 Exec MEMF_CLEAR / Requirement Qualification

Status: **STATIC READY / RUNTIME PENDING**

M2.10 keeps the M2.9 first-fit allocator and adds the first public requirement semantics for the single CHIP `MemHeader`:

- `MEMF_FAST` requests are rejected because no FAST region exists;
- `MEMF_CHIP` remains satisfiable by the existing region;
- `MEMF_CLEAR` zeroes the complete aligned allocation before `AllocMem()` returns.

Public Exec surface remains `AllocMem(-198)`, `FreeMem(-210)`, and `AvailMem(-216)`.

## Runtime semantic probe

The ROM initializes one 4096-byte CHIP region and seeds the beginning of its payload with nonzero data.

1. `AllocMem($20,MEMF_FAST)` must return NULL.
2. `AvailMem(MEMF_TOTAL)` must still report 4096 and the free-list must remain unchanged.
3. `AllocMem($20,MEMF_CHIP|MEMF_CLEAR)` must return `$5000`.
4. Every longword in `$5000..$501f` must be zero, including bytes that were explicitly pre-seeded nonzero.
5. `AvailMem(MEMF_TOTAL)` must report 4064.
6. `FreeMem($5000,$20)` must restore the original one-chunk 4096-byte region.

Diagnostic colours: red = running, blue = semantic failure, green = complete PASS.

## Static gate

```sh
make clean
make check
```

The checker verifies the V40.10 identity/header, memory LVOs, explicit FAST and CHIP|CLEAR probes, wrapper flag tests, clear loop, delegation to the M2.9 first-fit core, retained traversal/relink machinery, PASS/FAIL markers and final ROM checksum.

## Runtime gate

```sh
make qualify-m2_10
```

Target: FS-UAE A500 / 68000. Runtime PASS requires a stable green screen and normal emulator exit.

## Non-claims

M2.10 does not yet implement multiple `MemHeader` regions, general attribute ranking across regions, `MEMF_LARGEST`, or full `AvailMem()` flag semantics.

## Runtime record

- Date: pending
- Host: pending
- FS-UAE: pending
- CPU/model: A500 / 68000
- ROM identifier/hash: pending
- Diagnostic screen: pending
- Result: **PENDING**
