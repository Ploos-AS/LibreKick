# M2.2 Public Exec LVO Qualification

Status: **STATIC READY / RUNTIME PENDING**

M2.2 introduces the first public `exec.library` call surface in LibreKick: `Forbid()` at LVO `-132` and `Permit()` at LVO `-138`.

These offsets and the no-argument calling convention are part of the classic Exec ABI. The documented semantics are nested task-rescheduling suppression: each `Forbid()` must be matched by a `Permit()`, and the calls preserve registers.

## Scope

M2.2 provides:

- `SysBase` at `$00000004`, pointing to LibreKick's Exec base at `$00002200`;
- an Amiga-style `struct Library` header;
- a negative vector region large enough to include public LVOs through `-138`;
- public `Forbid()` vector at `-132(a6)`;
- public `Permit()` vector at `-138(a6)`;
- no-argument 68k ABI through A6;
- D/A-register-preserving implementations;
- nested state probe using a private byte initialized to `-1`, with the sequence `Forbid, Forbid, Permit` expected to leave state at `0`.

The private nesting byte is an implementation probe only. M2.2 does **not** yet claim a complete `struct ExecBase` layout, a scheduler, task switching, or full Exec semantic compatibility. Because no scheduler exists yet, the rescheduling side effect is not observable beyond nesting state.

## Static gate

```sh
make clean
make check
```

PASS requires:

- 512 KiB ROM and valid checksum;
- correct OVL handoff;
- `SysBase -> $00002200`;
- `lib_NegSize = 138`;
- version 40.2 header;
- six-byte `JMP absolute` entries at `-132` and `-138`;
- bootstrap calls through `jsr -132(a6)` and `jsr -138(a6)`;
- Forbid increments and Permit decrements the private signed nesting byte without using D/A registers.

## Runtime gate

```sh
make qualify-m2_2
```

A500/68000 interpretation:

- **green screen**: public LVO calls returned and nesting probe produced the expected state; runtime PASS;
- **red screen**: execution reached the public LVO probe but did not complete;
- **blue screen**: calls returned, but the nesting-state assertion failed;
- other state: failure earlier in bootstrap/init.

## References

The implementation is based on documented public Exec behavior and published LVO tables. No proprietary ROM implementation code is copied into LibreKick.

## Runtime record

- Date: pending
- Host: pending
- FS-UAE: pending
- CPU/model: A500 / 68000
- ROM identifier: pending
- Diagnostic screen: pending
- Result: **PENDING**
