# M2.9 Exec AllocMem First-Fit Qualification

Status: **STATIC READY / RUNTIME PENDING**

M2.9 extends the single-region M2.8 allocator so `AllocMem()` walks the complete address-sorted `MemChunk` free list instead of assuming the head chunk is large enough.

Public Exec surface retained:

- `AllocMem()` at **-198(a6)**;
- `FreeMem()` at **-210(a6)**;
- `AvailMem()` at **-216(a6)**.

## Qualified scope

The single 4 KiB CHIP region now supports:

- general first-fit traversal across multiple free chunks;
- skipping an undersized head chunk;
- splitting a fitting non-head chunk and relinking its predecessor;
- consuming a fitting non-head chunk whole and unlinking it cleanly;
- M2.8 address-sorted `FreeMem()` reinsertion and bidirectional coalescing;
- 8-byte request alignment and total-free accounting.

Multiple `MemHeader` regions, full requirement-mask filtering, `MEMF_CLEAR`, largest-block `AvailMem()` semantics and allocation metadata remain deferred.

## Runtime semantic probe

The ROM runs two fragmentation scenarios.

### Scenario 1 — non-head split

1. Allocate A=`$5000/$100`, B=`$5100/$200`, C=`$5300/$100`.
2. Free A and C, producing `$5000/$100 -> $5300/$D00`.
3. `AllocMem($180)` must skip the too-small `$5000` head and return `$5300`.
4. The selected second chunk is split, leaving `$5480/$B80` linked after the untouched `$5000/$100` head.
5. `AvailMem(MEMF_TOTAL)` must report `$C80`.
6. Free the allocation and B; the full `$5000/$1000` region must coalesce again.

### Scenario 2 — non-head whole-chunk unlink

1. Allocate `$100` then `$200`; free the first allocation.
2. The list is `$5000/$100 -> $5300/$D00`.
3. `AllocMem($D00)` must skip the head and consume the second chunk exactly.
4. The free list must retain only `$5000/$100`; `AvailMem(MEMF_TOTAL)` must report `$100`.
5. Free the exact allocation and B; the full 4096-byte region must be restored.

Diagnostic colours:

- **red** (`$F00`) = probe running / call failed to return;
- **blue** (`$00F`) = semantic validation failed;
- **green** (`$0F0`) = complete M2.9 semantic PASS.

## Static gate

```sh
make clean
make check
```

The checker verifies the M2.9 ROM identity, reset/OVL bootstrap, V40.9 header, memory LVO slots, expected call counts, first-fit traversal instructions, predecessor tracking, non-head relink paths, retained M2.8 coalescing, 68000 address-register `TST` regression guards, PASS/FAIL markers and the final ROM checksum.

## Runtime gate

```sh
make qualify-m2_9
```

Target: FS-UAE A500 / 68000. Runtime PASS requires a stable green screen and normal manual emulator exit.

## Runtime record

- Date: pending
- Host: pending
- FS-UAE: pending
- CPU/model: A500 / 68000
- ROM identifier/hash: pending
- Diagnostic screen: pending
- Result: **PENDING**
