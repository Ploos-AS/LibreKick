# M2.0 Exec Foundation Qualification

Status: **STATIC READY / RUNTIME PENDING**

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

A visible green screen proves control flow has passed SysBase and descriptor initialization, but direct debugger inspection should be used when available for stronger evidence.

## Runtime record

- Date: pending
- Host: pending
- FS-UAE: pending
- CPU/model: A500 / 68000
- ROM SHA-256: pending
- Green `COLOR00` marker: pending
- SysBase `$00000004`: pending
- Descriptor `EX01`: pending
- Result: **PENDING**
