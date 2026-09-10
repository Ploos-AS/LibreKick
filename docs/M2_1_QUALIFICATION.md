# M2.1 Library ABI Foundation Qualification

Status: **STATIC READY / RUNTIME PENDING**

M2.1 replaces the private M2.0 descriptor with an Amiga-style `struct Library` positive region and a real negative-vector call mechanism. It deliberately does **not** claim complete `exec.library` ABI or semantic compatibility yet.

## What M2.1 establishes

After reset, LibreKick:

1. places the library base at `$00002100` and writes that address to canonical `SysBase` location `$00000004`;
2. initializes the documented `struct Library` header shape: `Node`, flags/pad, negative/positive sizes, version/revision, ID string, checksum field and open count;
3. identifies the base as `exec.library`, target version 40.1;
4. installs a six-byte Amiga-style negative vector at `-6(a6)` containing `JMP absolute` into ROM;
5. loads A6 with the library base and executes `JSR -6(a6)`;
6. the probe routine returns `LKV1` (`$4c4b5631`) in D0;
7. bootstrap stores that result at chip RAM `$00001040`;
8. writes `$0F0F` to `COLOR00` as the visible magenta success marker and enters a controlled idle loop.

The `-6` vector is a **LibreKick private probe for M2.1**. It is not presented as a public Exec LVO. Public Exec vectors will only be added once their documented offsets, register ABI and semantics are implemented and tested.

## Static gate

```sh
make clean
make check
```

PASS requires:

- exact 512 KiB image;
- reset SP `$0007fffc`, reset PC `$00f80008`;
- `SysBase -> $00002100` bootstrap sequence;
- Library sizes/version fields (`NegSize=6`, `PosSize=34`, version 40.1);
- negative vector encoding at `$000020fa` targeting ROM `$00f80300`;
- actual `lea $2100,a6 ; jsr -6(a6)` call sequence;
- probe routine returning `LKV1`;
- result-store and magenta marker sequences;
- final ROM checksum `$ffffffff`.

## Runtime gate

```sh
make qualify-m2_1
```

PASS on A500/68000 requires:

- FS-UAE accepts/maps the 512 KiB ROM;
- stable **magenta** screen (`COLOR00=$0F0F`);
- no reset loop or illegal-instruction failure;
- CPU reaches the final idle loop;
- when debugger inspection is available, `$00000004 == $00002100`;
- when debugger inspection is available, `$00001040 == $4c4b5631` (`LKV1`).

The magenta marker occurs only after the negative-vector call returns, so it is direct visual control-flow evidence that the vector mechanism executed and returned. Direct RAM inspection remains the stronger evidence for the return value.

## Non-claims

M2.1 does not yet provide scheduler semantics, memory allocation, signals, messages, interrupts, devices, DOS, Intuition, or a complete public Exec LVO table. It is an ABI-mechanism foundation, not an AmigaOS 3.1-compatible kernel milestone by itself.

## Runtime record

- Date: pending
- Host: pending
- FS-UAE: pending
- CPU/model: A500 / 68000
- ROM SHA-256: pending
- Magenta `COLOR00` marker: pending
- `SysBase`: pending
- `LKV1` result at `$00001040`: pending
- Result: **PENDING**
