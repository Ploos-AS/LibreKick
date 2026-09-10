# M2.8 Exec Sorted Free-List Qualification

Status: **STATIC READY / RUNTIME PENDING**

M2.8 extends the single-region M2.7 allocator with an address-sorted `MemChunk` free list and bidirectional adjacent coalescing in `FreeMem()`.

Public Exec surface retained:

- `AllocMem()` at **-198(a6)**;
- `FreeMem()` at **-210(a6)**;
- `AvailMem()` at **-216(a6)**.

## Qualified scope

The single 4 KiB CHIP region now supports:

- multiple simultaneous free chunks;
- address-sorted `FreeMem()` insertion;
- successor coalescing;
- predecessor coalescing;
- arbitrary-order freeing for the qualified A/B/C fragmentation pattern;
- restoration of the entire region to one `MemChunk`;
- 8-byte request alignment and total-free accounting inherited from M2.7.

`AllocMem()` still consumes the first suitable head chunk in the qualified scenarios. General first-fit traversal across multiple free chunks, multiple `MemHeader` regions, full requirement-mask filtering, `MEMF_CLEAR`, largest-block semantics and allocation metadata remain deferred.

## Runtime semantic probe

The ROM initializes `$5000..$5fff` as one 4096-byte free chunk and allocates:

1. A: `$5000`, size `$100`;
2. B: `$5100`, size `$80`;
3. C: `$5180`, size `$40`;
4. residual free chunk starts at `$51c0`.

It then deliberately frees out of allocation order:

1. free A: free list must become `$5000 -> $51c0`;
2. free C: C is inserted between A and the residual chunk, then successor-coalesced into `$5180..$5fff`;
3. free B: B lies exactly between the two free chunks and must coalesce with both, restoring one `$5000` / 4096-byte chunk.

The probe finally allocates and frees `$200` at `$5000` and verifies `AvailMem(MEMF_TOTAL) == 4096` again.

Diagnostic colours:

- **red** (`$F00`) = probe running / call failed to return;
- **blue** (`$00F`) = semantic validation failed;
- **green** (`$0F0`) = complete M2.8 semantic PASS.

## Static gate

```sh
make clean
make check
```

The checker verifies the M2.8 ROM identity, A500 reset/OVL bootstrap, V40.8 header, memory LVO slots, MemHeader region constants, expected AllocMem/FreeMem/AvailMem call counts, multi-fragment runtime assertions, sorted-list traversal, both coalescing paths, 68000 address-register-TST regression guards, PASS/FAIL markers and ROM checksum.

## Runtime gate

```sh
make qualify-m2_8
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
