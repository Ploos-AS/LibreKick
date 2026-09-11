# M2.14 Exec Dynamic Allocation Qualification

Status: **STATIC READY / RUNTIME PENDING**

M2.14 extends the M2.13 `AddMemList()` slice so `AllocMem()` and `FreeMem()` can actually use the dynamically registered FAST region.

## Qualified scope

The runtime keeps the existing static CHIP and FAST regions, registers one dynamic FAST region with `AddMemList()`, then verifies:

- static FAST is tried first;
- if static FAST cannot satisfy the request, `AllocMem()` falls back to the registered dynamic FAST region;
- `MEMF_CLEAR` still zeroes a dynamic allocation;
- dynamic `mh_First` and `mh_Free` accounting changes after allocation;
- `FreeMem()` routes an address in the dynamic region back to its own free-list core;
- freeing restores the dynamic region to its original one-chunk state;
- freeing the exhausted static FAST allocation restores that region independently;
- `AvailMem(MEMF_FAST)` observes the combined static + dynamic free bytes.

The qualified dynamic region remains the M2.13 region at `$9000..$9fff`, with a 32-byte `MemHeader` and usable payload beginning at `$9020`.

## Runtime semantic probe

1. Register `$9000/$1000` as logical `MEMF_FAST` using `AddMemList()`.
2. Confirm FAST free total is `$1000 + $FE0 = $1FE0`.
3. Allocate `$1000` FAST, consuming the static FAST region completely.
4. Allocate `$100` FAST|CLEAR; this must fall back to the dynamic region and return `$9020`.
5. Verify the complete `$100` allocation is zero and dynamic free bytes become `$EE0`.
6. Free `$9020/$100`; dynamic free bytes must return to `$FE0` with first chunk at `$9020`.
7. Free the static `$7000/$1000` block.
8. Confirm combined FAST free total returns to `$1FE0`.

Diagnostic colours: red = running, blue = semantic failure, green = complete PASS.

## Static gate

```sh
make clean
make check
```

The checker verifies the public memory LVOs, `AddMemList()` call, static-to-dynamic allocation fallback, dynamic registration-slot/attribute checks, dynamic free routing, relocated allocator/free cores, runtime constants, PASS/FAIL markers and final ROM checksum.

## Runtime gate

```sh
make qualify-m2_14
```

Target: FS-UAE A500 / 68000. Runtime PASS requires a stable green screen and normal manual emulator exit.

## Non-claims

M2.14 still qualifies only one dynamically registered region. It does not yet implement a general linked `MemList` traversal across arbitrary numbers of dynamically registered `MemHeader` entries, priority ordering, or dynamic-region `MEMF_LARGEST` scanning.

## Runtime record

- Date: pending
- Host: pending
- FS-UAE: pending
- CPU/model: A500 / 68000
- ROM identifier/hash: pending
- Diagnostic screen: pending
- Result: **PENDING**
