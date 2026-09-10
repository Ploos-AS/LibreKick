# M2.7 Exec MemHeader/MemChunk Qualification

Status: **PASS**

M2.7 replaces the artificial two-block M2.6 pool with the first real Exec-style free-memory structure:

- one 4 KiB CHIP region;
- a `MemHeader` subset using the canonical `mh_Attributes`, `mh_First`, `mh_Lower`, `mh_Upper`, and `mh_Free` offsets;
- a `MemChunk` free-list node `{mc_Next, mc_Bytes}`;
- `AllocMem()` at **-198(a6)**;
- `FreeMem()` at **-210(a6)**;
- `AvailMem()` at **-216(a6)**.

## Qualified scope

This slice intentionally qualifies one active first-fit free chunk with:

- 8-byte request alignment;
- front splitting;
- total free-byte accounting through `mh_Free` / `AvailMem()`;
- LIFO head reinsertion by `FreeMem()`;
- adjacent-next coalescing;
- complete-region restoration when allocations are freed in reverse order.

Arbitrary sorted reinsertion, multiple simultaneous free chunks, arbitrary-order coalescing, multiple `MemHeader` regions, `MEMF_CLEAR`, largest-block semantics and full requirement-mask filtering are deferred to later memory milestones.

## Runtime semantic probe

The ROM initializes `$5000..$5fff` as one 4096-byte free `MemChunk`, then verifies:

1. `AvailMem(MEMF_TOTAL)` returns 4096.
2. `AllocMem(0x100,MEMF_CHIP)` returns `$5000` and free bytes become 3840.
3. `AllocMem(0x80,MEMF_CHIP)` returns `$5100`; `mh_First` advances to `$5180`.
4. Freeing the second allocation reinserts it before `$5180` and coalesces the adjacent chunks.
5. Freeing the first allocation restores one `$5000` / 4096-byte free chunk.
6. A new 0x40-byte allocation reuses `$5000`, and freeing it restores the full region again.

Diagnostic colours:

- **red** (`$F00`) = probe running / a call failed to return;
- **blue** (`$00F`) = a call returned but semantic validation failed;
- **green** (`$0F0`) = complete M2.7 semantic PASS.

## Static gate

```sh
make clean
make check
```

The checker verifies reset vectors, OVL handoff, V40.7 library header, public LVO slots through `AvailMem`, canonical `MemHeader` setup, allocator call counts, 8-byte-alignment code, the M2.5 word-branch PC-base regression guard, absence of illegal address-register `TST` encodings, PASS/FAIL markers and the ROM checksum.

## Runtime gate

```sh
make qualify-m2_7
```

Target: FS-UAE A500 / 68000. Runtime PASS requires a stable green screen and normal manual emulator exit.

## Runtime record

- Date: 2026-09-10
- Host: Linux x86-64
- FS-UAE: 3.2.35
- CPU/model: A500 / 68000
- ROM size: 524288 bytes
- FS-UAE ROM identifier: `f73d2f83`
- Static checker: **PASS** — `Exec AllocMem/FreeMem/AvailMem; one-region MemHeader/MemChunk split+coalesce slice; checksum=0xffffffff`
- Diagnostic screen: stable **green** (`$0F0`)
- Emulator exit: normal (`UAE: Calling uae_quit` / `UAE: Stopping`)
- Result: **PASS**
