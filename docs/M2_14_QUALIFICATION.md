# M2.14 Exec Dynamic Allocation Qualification

Status: **PASS**

M2.14 extends the M2.13 `AddMemList()` slice so `AllocMem()` and `FreeMem()` can actually use the dynamically registered FAST region.

## Qualified scope

The runtime keeps the existing static CHIP and FAST regions, registers one dynamic FAST region with `AddMemList()`, then verifies:

- static FAST is tried first;
- if static FAST cannot satisfy the request, `AllocMem()` falls back to the registered dynamic FAST region;
- `MEMF_CLEAR` zeroes the complete dynamic allocation;
- dynamic `mh_First` and `mh_Free` accounting changes after allocation;
- `FreeMem()` routes an address in the dynamic region back to its own free-list core;
- freeing restores the dynamic region to its original one-chunk state;
- freeing the exhausted static FAST allocation restores that region independently;
- `AvailMem(MEMF_FAST)` observes the combined static + dynamic free bytes.

The qualified dynamic region is `$9000..$9fff`, with a 32-byte `MemHeader` and usable payload beginning at `$9020`.

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

The checker also contains regressions for two routing bugs found during qualification: dynamic `AllocMem()` must preserve the requested size while inspecting attributes, and dynamic `FreeMem()` must preserve public `D0=size` while checking the registration slot.

## Runtime gates

Local:

```sh
make qualify-m2_14
```

Automated GitHub Actions:

- workflow: `FS-UAE runtime qualification`
- run: `34747574347`
- runner: Ubuntu 24.04
- FS-UAE package: 3.1.66
- screenshot: 960x540
- green ratio: 0.8911
- blue ratio: 0.0000
- red ratio: 0.0000
- result: PASS
- evidence artifact: `fs-uae-runtime-qualification`
- artifact SHA-256: `0fa692081f3bdd6bec8e94a9674ea218dd7e594d39501b4bfe07c129fe5f6079`

The same fixed ROM also produced a stable green screen in the local FS-UAE A500 qualification run.

## Non-claims

M2.14 qualifies one dynamically registered region. It does not yet implement a general linked `MemList` traversal across arbitrary numbers of dynamically registered `MemHeader` entries, priority ordering, or dynamic-region `MEMF_LARGEST` scanning.

## Runtime record

- Date: 2026-09-13
- CPU/model: A500 / 68000
- ROM size: 524288 bytes
- checksum gate: `0xffffffff`
- GitHub qualification HEAD: `50f99eff4497fd3eca02f59985326b1a11321589`
- Diagnostic screen: green
- Result: **PASS**
