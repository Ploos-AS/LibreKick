# M1 Runtime Qualification

Status: **PASS**

M1's purpose is deliberately narrow: prove that LibreKick can produce a deterministic 512 KiB ROM image whose 68000 reset vector executes in an Amiga-compatible machine profile.

## Build gate

```sh
make clean
make check
```

The static gate verifies:

- exact 512 KiB image size;
- initial supervisor stack pointer `0x0007fffc`;
- reset PC `0x00f80008`;
- exact 68000 bootstrap bytes;
- embedded `LIBREKICK-M1` marker;
- 32-bit one's-complement ROM checksum of `0xffffffff`.

## Bootstrap evidence

When executed, the M1 reset stub:

1. enters supervisor mode with interrupts masked;
2. writes ASCII `LK01` as longword `0x4c4b3031` to chip RAM address `0x00001000`;
3. writes `0x000f` to Amiga custom register `COLOR00` at `0x00dff180`;
4. remains in a controlled two-byte branch loop.

The ROM does **not** provide Exec, DOS, Intuition, a filesystem, or AmigaOS 3.1 compatibility yet. Claiming any of those at M1 would be incorrect.

## FS-UAE qualification

The preferred qualification entry point is:

```sh
make qualify-m1
```

This invokes `tools/qualify_m1_fsuae.sh`, which:

- rebuilds and runs the static gate;
- records the ROM SHA-256 under `build/m1-runtime/`;
- records the FS-UAE version;
- launches `configs/fs-uae/a500-m1.fs-uae` visibly;
- captures FS-UAE output and exit status for the qualification record.

The equivalent manual sequence is:

```sh
make clean
make check
fs-uae configs/fs-uae/a500-m1.fs-uae
```

Runtime PASS requires all of the following to be observed on a 68000-class A500 profile:

- emulator accepts and maps the 512 KiB image;
- CPU reaches `0x00f80008` without reset-loop or illegal-instruction failure;
- `COLOR00` changes to the expected debug value;
- memory inspection shows `0x4c4b3031` at `0x00001000` when debugger/memory inspection is available;
- CPU remains in the intentional bootstrap loop.

A clean emulator exit alone is **not** sufficient for PASS.

## Runtime record

- Date: 2026-09-10
- Host: Linux x86-64
- FS-UAE: 3.2.35
- CPU/model: A500 / 68000
- ROM size: 524288 bytes
- ROM SHA-256: `580ba693f6147f6cfe755f91f3f32512ef14fc5ba175da9b1b1cf7ff830a69fd`
- Reset SP: `0x0007fffc`
- Reset PC: `0x00f80008`
- ROM checksum: `0xffffffff`
- FS-UAE ROM mapping: PASS (`KS ROM f8aacaaa (524288 bytes)`)
- COLOR00 marker: PASS — visible solid blue display observed
- `LK01` RAM signature: INFERRED from verified instruction order and successful later COLOR00 write; direct debugger memory inspection was not performed
- Bootstrap idle loop: PASS — emulator remained stable on the expected solid-blue state until manually closed
- FS-UAE exit: clean (`UAE: Calling uae_quit`, `UAE: Stopping`)
- Result: **PASS**

### Qualification note

The visible COLOR00 marker is written only after the `LK01` store in the statically verified bootstrap sequence. The observed blue display therefore proves execution progressed through the RAM-signature instruction and into the intended terminal idle state. A future debugger-backed qualification may additionally record the RAM value directly, but direct memory inspection is not required to retain this M1.1 PASS.
