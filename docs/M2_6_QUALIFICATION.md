# M2.6 Exec Memory Qualification

Status: **STATIC READY / RUNTIME PENDING**

M2.6 starts Exec memory management with the public V40-compatible entry points:

- `AllocMem(byteSize, attributes)` at **-198(a6)** — D0/D1, result D0
- `FreeMem(memoryBlock, byteSize)` at **-210(a6)** — A1/D0

The public offsets and register ABI follow the published Exec autodocs/function table.

## Scope

This first slice intentionally uses a deterministic internal pool of two 256-byte Chip RAM blocks. Requests from 1 through 256 bytes consume one block; zero-sized and oversized requests fail with NULL. `FreeMem` releases either managed block so it can be reused. The attributes argument is accepted but not interpreted yet.

This is deliberately **not** a claim of full Amiga Exec memory semantics. Full `MemHeader`/`MemChunk`, arbitrary-size splitting/coalescing, memory attributes, MEMF_CLEAR, multiple regions and AvailMem come in later milestones.

## Runtime semantic probe

The A500/68000 ROM performs:

1. `AllocMem(32,0)` -> first block at `$00004000`;
2. `AllocMem(16,0)` -> second block at `$00004100`;
3. `AllocMem(8,0)` with both occupied -> NULL;
4. `FreeMem($00004000,32)`;
5. `AllocMem(64,0)` -> reuses `$00004000`.

Diagnostic colours:

- red = probe entered;
- orange/yellow/cyan-blue = progressive allocation/free checkpoints;
- blue = returned value failed a semantic assertion;
- green = complete M2.6 PASS.

## Static gate

```sh
make clean
make check
```

The checker validates ROM size/reset vectors, OVL handoff, V40.6 library header, AllocMem/FreeMem vector slots and targets, expected runtime call sites, success/failure markers and final one's-complement checksum `$ffffffff`.

## Runtime gate

```sh
make qualify-m2_6
```

Target: FS-UAE A500 / 68000. Runtime PASS requires a stable green screen and clean manual emulator exit.

## Runtime record

- Date: pending
- Host: pending
- FS-UAE: pending
- CPU/model: A500 / 68000
- ROM identifier/hash: pending
- Diagnostic screen: pending
- Result: **PENDING**
