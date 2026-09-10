# M2.1 Library ABI Foundation Qualification

Status: **STATIC READY / RUNTIME DIAGNOSTIC PENDING**

M2.1 replaces the private M2.0 descriptor with an Amiga-style `struct Library` positive region and a real negative-vector call mechanism. It deliberately does **not** claim complete `exec.library` ABI or semantic compatibility yet.

## M2.1a diagnostic revision

The original single magenta success marker proved ambiguous in the first FS-UAE run. M2.1a therefore uses two deliberately simple checkpoint colours around the vector call:

- **red** (`COLOR00=$F00`) immediately before `JSR -6(a6)`;
- **green** (`COLOR00=$0F0`) only after the vector returns and D0 has been stored at `$00001040`.

This makes the runtime result binary and easy to interpret on the same FS-UAE setup where green was already verified during M2.0 qualification.

## What M2.1a establishes

After reset, LibreKick:

1. places the library base at `$00002100` and writes that address to canonical `SysBase` location `$00000004`;
2. initializes the documented `struct Library` header shape: `Node`, flags/pad, negative/positive sizes, version/revision, ID string, checksum field and open count;
3. identifies the base as `exec.library`, target version 40.1;
4. installs a six-byte Amiga-style negative vector at `-6(a6)` containing `JMP absolute` to ROM `$00f80300`;
5. writes the red pre-call checkpoint;
6. loads A6 with the library base and executes `JSR -6(a6)`;
7. the probe routine returns `LKV1` (`$4c4b5631`) in D0;
8. bootstrap stores that result at chip RAM `$00001040`;
9. writes the green post-return checkpoint and enters a controlled idle loop.

The `-6` vector remains a **LibreKick private probe**. It is not presented as a public Exec LVO. Public Exec vectors will only be added once their documented offsets, register ABI and semantics are implemented and tested.

## Static gate

```sh
make clean
make check
```

PASS requires the expected 512 KiB image, reset vectors, Library fields, six-byte negative vector, `lea $2100,a6 ; jsr -6(a6)`, probe routine, red-before/green-after checkpoints, and final ROM checksum `$ffffffff`.

## Runtime gate

```sh
make qualify-m2_1
```

Interpretation on A500/68000:

- **green screen**: vector call returned successfully; M2.1a runtime PASS;
- **red screen**: initialization reached the call site but `JSR -6(a6)` did not return; investigate vector/probe execution;
- any other stable colour/state: runtime FAIL/BLOCKED; investigate earlier initialization or display state.

When debugger inspection is available, stronger evidence is `$00000004 == $00002100` and `$00001040 == $4c4b5631` (`LKV1`).

## Non-claims

M2.1a does not yet provide scheduler semantics, memory allocation, signals, messages, interrupts, devices, DOS, Intuition, or a complete public Exec LVO table. It is an ABI-mechanism foundation, not an AmigaOS 3.1-compatible kernel milestone by itself.

## Runtime record

- Date: pending
- Host: pending
- FS-UAE: pending
- CPU/model: A500 / 68000
- Diagnostic screen: pending
- `SysBase`: pending
- `LKV1` result at `$00001040`: pending
- Result: **PENDING**
