# M1 Runtime Qualification

Status: **STATIC PASS / RUNTIME READY FOR QUALIFICATION**

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

- Date: pending
- Host: pending
- FS-UAE: pending
- CPU/model: A500 / 68000
- ROM SHA-256: pending
- COLOR00 marker: pending
- `LK01` RAM signature: pending
- Bootstrap idle loop: pending
- Result: **PENDING**
