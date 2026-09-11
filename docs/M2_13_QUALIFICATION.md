# M2.13 Exec AddMemList Qualification

Status: **PASS**

M2.13 adds the first public `AddMemList()` slice to LibreKick.

Public Exec surface added:

- `AddMemList()` at **-618(a6)**;
- ABI: `D0=size`, `D1=attributes`, `D2=priority`, `A0=base`, `A1=name`.

The implementation creates a `MemHeader` in the first 32 bytes of the supplied memory area and creates one initial `MemChunk` from the remaining bytes. The dynamic header pointer is published in a private M2.13 registration slot so `AvailMem()` can include the new region in total-free accounting.

## Qualified scope

The runtime probe starts with the M2.12 static logical CHIP and FAST regions, then registers one additional logical FAST region:

- base `$9000`;
- size `$1000`;
- attributes `MEMF_FAST`;
- priority `5`;
- persistent name string in ROM.

The resulting dynamic layout must be:

- `MemHeader` at `$9000`;
- first/lower address `$9020`;
- upper address `$A000`;
- free bytes `$FE0`;
- one initial `MemChunk` at `$9020` with `mc_Next = NULL` and `mc_Bytes = $FE0`.

The probe also verifies that FAST total-free accounting changes from `$1000` to `$1FE0`, and combined total free changes from `$2000` to `$2FE0`.

## Static gate

```sh
make clean
make check
```

The checker verifies the extended negative library size, AddMemList LVO slot/target, exact `JSR -618(a6)` runtime call, MemHeader/Node field writes, initial MemChunk creation, dynamic registration publication, dynamic `AvailMem()` total contribution, PASS/FAIL markers, 68000 regression guards and final ROM checksum.

## Runtime gate

```sh
make qualify-m2_13
```

Target: FS-UAE A500 / 68000. Runtime PASS requires a stable green screen and normal manual emulator exit.

## Non-claims

M2.13 intentionally does **not** yet qualify:

- allocation from dynamically registered regions;
- arbitrary numbers of dynamic regions;
- priority ordering among multiple `MemHeader` entries;
- dynamic-region participation in fragmented `MEMF_LARGEST` scans;
- physical Fast RAM discovery.

Those are follow-up slices, starting with M2.14 dynamic allocation/routing.

## Runtime record

- Date: 2026-09-11
- Host: Linux x86-64
- FS-UAE: 3.2.35
- CPU/model: A500 / 68000
- ROM size: 524288 bytes
- ROM identifier/hash: `f1fbf6c4` (FS-UAE KS ROM identifier)
- Static checker: PASS
- ROM checksum: `0xffffffff`
- Diagnostic screen: stable green PASS marker
- Emulator exit: normal manual exit (`UAE: Calling uae_quit` / `UAE: Stopping`)
- Result: **PASS**
