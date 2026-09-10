# M2.1 Library ABI Foundation Qualification

Status: **STATIC READY / M2.1C RUNTIME PENDING**

M2.1 replaces the private M2.0 descriptor with an Amiga-style `struct Library` positive region and a real negative-vector call mechanism. It deliberately does **not** claim complete `exec.library` ABI or semantic compatibility yet.

## Diagnostic history

M2.1a added red-before/green-after checkpoints around `JSR -6(a6)`.

M2.1b then added an explicit CIAA OVL handoff, but used the wrong polarity: `BSET #0,CIAA_PRA` leaves ROM overlay enabled. The observed red screen was therefore expected: bootstrap reached the pre-call checkpoint, but the CPU fetched the negative vector from the still-overlaid low ROM mapping instead of Chip RAM.

M2.1c corrects the handoff:

1. `MOVE.B #$03,CIAA_DDRA` configures PA0 (OVL) and PA1 as outputs;
2. `BCLR #0,CIAA_PRA` clears OVL so Chip RAM is mapped at address `$000000`;
3. LibreKick then installs the RAM-resident negative vector at `$000020fa` and calls it through A6.

## M2.1c runtime path

After reset LibreKick:

1. enters supervisor mode with interrupts masked;
2. disables the ROM overlay correctly;
3. places the library base at `$00002100` and writes it to canonical `SysBase` location `$00000004`;
4. initializes the `struct Library` foundation;
5. installs a six-byte negative vector at `-6(a6)` containing `JMP $00f80300`;
6. writes **red** (`COLOR00=$F00`) immediately before the call;
7. executes `JSR -6(a6)`;
8. the ROM probe returns `LKV1` (`$4c4b5631`) in D0;
9. bootstrap stores D0 at `$00001040`;
10. writes **green** (`COLOR00=$0F0`) and enters the final idle loop.

The `-6` vector remains a **LibreKick private probe**. It is not presented as a public Exec LVO.

## Static gate

```sh
make clean
make check
```

PASS requires the expected 512 KiB image, reset vectors, correct CIAA `DDRA` + `BCLR OVL` sequence, Library fields, six-byte negative vector, `lea $2100,a6 ; jsr -6(a6)`, probe routine, red-before/green-after checkpoints, and final ROM checksum `$ffffffff`.

## Runtime gate

```sh
make qualify-m2_1
```

Interpretation on A500/68000:

- **green screen**: corrected OVL handoff succeeded and the RAM vector returned; M2.1c runtime PASS;
- **red screen**: low-memory handoff/init reached the call site, but the vector/probe did not return;
- any other stable colour/state: failure before the pre-call checkpoint.

When debugger inspection is available, stronger evidence is `$00000004 == $00002100`, bytes `4e f9 00 f8 03 00` at `$000020fa`, and `$00001040 == $4c4b5631` (`LKV1`).

## Non-claims

M2.1c does not yet provide scheduler semantics, memory allocation, signals, messages, interrupts, devices, DOS, Intuition, or a complete public Exec LVO table.

## Runtime record

- Date: pending
- Host: pending
- FS-UAE: pending
- CPU/model: A500 / 68000
- Diagnostic screen: pending
- `SysBase`: pending
- `LKV1` result at `$00001040`: pending
- Result: **PENDING**
