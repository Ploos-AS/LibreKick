# M2.0 Exec Foundation Qualification

Status: **PASS**

M2.0 is the first slice of the M2 core-runtime milestone. It does **not** claim a complete or ABI-compatible `exec.library` yet.

## What M2.0 establishes

After reset, the 68000 bootstrap:

1. enters supervisor mode with interrupts masked;
2. writes `$00002000` to absolute address `$00000004`, the canonical Amiga `SysBase` pointer location;
3. initializes a small LibreKick-owned kernel descriptor at `$00002000`;
4. records the target version as 40.0 and bootstrap RAM bounds;
5. writes `$0F0` to `COLOR00` as the visible M2.0 runtime marker;
6. remains in a controlled idle loop.

The descriptor currently contains:

- `+0x00`: `EX01` signature (`0x45583031`)
- `+0x04`: target version `40`
- `+0x06`: revision `0`
- `+0x08`: low bootstrap-reserved RAM boundary `$00000400`
- `+0x0c`: initial top-of-RAM marker `$0007fffc`

This structure is private to LibreKick M2.0 and is **not** asserted to match the public `ExecBase` ABI yet. Later M2 slices will replace it with documented ABI-compatible structures and callable Exec entry points.

## Static gate

```sh
make clean
make check
```

PASS requires:

- exact 512 KiB ROM size;
- reset SP `$0007fffc`;
- reset PC `$00f80008`;
- exact M2.0 68000 bootstrap byte sequence;
- `LIBREKICK-M2.0` marker;
- one's-complement ROM checksum `$ffffffff`.

## Runtime gate

```sh
make qualify-m2
```

On the A500/68000 FS-UAE profile, PASS requires:

- ROM accepted and mapped;
- stable **green** screen (`COLOR00=$0F0`);
- no reset loop or illegal-instruction failure;
- when debugger/memory inspection is available, `$00000004 == $00002000`;
- descriptor at `$00002000` begins with `EX01`;
- CPU remains in the intentional final idle loop.

A visible green screen proves control flow has passed SysBase and descriptor initialization. Direct debugger inspection is stronger evidence when available, but was not required for this M2.0 visual qualification.

## Runtime record

- Date: 2026-09-10
- Host: Linux x86-64
- FS-UAE: 3.2.35
- CPU/model: A500 / 68000
- ROM: 524288 bytes; FS-UAE identified KS ROM `a9ebff9e`
- Green `COLOR00` marker: **observed**
- SysBase `$00000004`: **inferred from statically verified instruction order before observed COLOR00 marker; not directly inspected**
- Descriptor `EX01`: **inferred from statically verified instruction order before observed COLOR00 marker; not directly inspected**
- Emulator exit: clean manual quit (`UAE: Calling uae_quit`, `UAE: Stopping`)
- Result: **PASS**

## Evidence boundary

This PASS proves the M2.0 bootstrap reaches the Exec-foundation state and remains stable in FS-UAE. It does **not** prove full `ExecBase` layout compatibility, callable Exec vectors, multitasking, interrupts, memory allocation APIs, devices, DOS, or Workbench compatibility.
