# M2.11 Exec Multi-MemHeader Qualification

Status: **PASS**

M2.11 extends the M2.10 allocator from one logical CHIP region to two logical Exec memory regions:

- CHIP: `MemHeader` at `$4800`, region `$5000..$5fff`, 4096 bytes;
- FAST: `MemHeader` at `$4a00`, region `$7000..$7fff`, 4096 bytes.

The A500 runtime target is used to qualify Exec attribute routing and allocator semantics. The second region is a logical `MEMF_FAST` test region in ordinary addressable RAM; this milestone does **not** claim that the A500 hardware physically provides Fast RAM.

Public Exec surface remains:

- `AllocMem()` at **-198(a6)**;
- `FreeMem()` at **-210(a6)**;
- `AvailMem()` at **-216(a6)**.

## Qualified scope

M2.11 adds:

- region selection by `MEMF_CHIP` / `MEMF_FAST`;
- deterministic CHIP preference when neither region bit is requested;
- rejection of simultaneous CHIP|FAST requirements because no one region satisfies both;
- independent first-fit free lists and free-byte accounting for both regions;
- address-based `FreeMem()` routing back to the owning logical region;
- `MEMF_CLEAR` on FAST allocations as well as CHIP allocations;
- `AvailMem()` filtering for CHIP, FAST and combined total-free bytes.

The per-region allocator/free-list implementation inherits the M2.9 first-fit traversal and M2.8 sorted/coalescing behavior.

## Runtime semantic probe

The ROM verifies:

1. `AvailMem(MEMF_CHIP) == 4096`.
2. `AvailMem(MEMF_FAST) == 4096`.
3. `AvailMem(MEMF_TOTAL) == 8192`.
4. `AllocMem($40,MEMF_CHIP)` returns `$5000`.
5. `AllocMem($80,MEMF_FAST|MEMF_CLEAR)` returns `$7000` and the complete aligned block is zero.
6. CHIP/FAST/total free-byte counts decrease independently and sum correctly.
7. `AllocMem($20,MEMF_CHIP|MEMF_FAST)` returns NULL without changing allocator state.
8. A request with no CHIP/FAST bit uses the deterministic CHIP preference.
9. `FreeMem()` routes blocks to the correct region and restores both regions to one full 4096-byte chunk.
10. Final CHIP, FAST and combined totals return to 4096, 4096 and 8192.

Diagnostic colours: red = running, blue = semantic failure, green = complete PASS.

## Static gate

```sh
make clean
make check
```

The checker verifies both `MemHeader` initializations and attributes, public memory LVOs, CHIP/FAST allocation/free dispatch, relocated per-region cores, CLEAR handling, AvailMem region accounting, runtime probe call coverage, PASS/FAIL markers and final ROM checksum.

Result: **PASS**.

## Runtime gate

```sh
make qualify-m2_11
```

Target: FS-UAE A500 / 68000. Runtime PASS requires a stable green screen and normal manual emulator exit.

Result: **PASS**.

## Non-claims

M2.11 does not yet implement physical Fast RAM discovery, `AddMemList()`, arbitrary numbers of dynamically registered `MemHeader` regions, region priority/ranking, `MEMF_LARGEST`, or full `AvailMem()` semantics.

## Runtime record

- Date: 2026-09-11
- Host: Linux x86-64
- FS-UAE: 3.2.35
- CPU/model: A500 / 68000
- ROM size: 524288 bytes
- ROM identifier: FS-UAE `bf705e65`
- Static checker: **PASS** — `Exec two-region CHIP/FAST MemHeader routing + CLEAR + AvailMem filtering; checksum=0xffffffff`
- Diagnostic screen: stable green (`$0F0`)
- Emulator shutdown: normal (`UAE: Calling uae_quit` / `UAE: Stopping`)
- Result: **PASS**
