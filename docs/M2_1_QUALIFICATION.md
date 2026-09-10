# M2.1 Library ABI Foundation Qualification

Status: **STATIC READY / M2.1B RUNTIME PENDING**

M2.1 replaces the private M2.0 descriptor with an Amiga-style `struct Library` positive region and a real negative-vector call mechanism. It deliberately does **not** claim complete `exec.library` ABI or semantic compatibility yet.

## M2.1b diagnosis: low-memory ROM overlay

The M2.1a run did not show either the red pre-call or green post-return marker. The important architectural difference from M2.0 is that M2.1 attempts to fetch executable code from the negative vector at low address `$000020fa`.

At reset, Amiga ROM overlay maps Kickstart into the low address range used for the initial vectors. M2.0 could write bookkeeping data to low RAM and continue executing from `$00f8xxxx` without ever fetching instructions from the low-memory vector. M2.1 is the first milestone that needs low memory to be readable as chip RAM code.

M2.1b therefore performs an explicit CIAA OVL handoff before installing or calling the RAM-resident library vector:

1. set CIAA PRA bit 0 high (`$00bfe001`);
2. configure CIAA DDRA bit 0 as an output (`$00bfe201`);
3. only then create `SysBase`, the Library header and the negative vector in chip RAM.

The ROM continues executing from its normal `$00f8xxxx` mapping while low memory becomes chip RAM.

## M2.1b runtime checkpoints

After the OVL handoff LibreKick:

1. writes `$00002100` to canonical `SysBase` location `$00000004`;
2. initializes the documented `struct Library` header shape;
3. installs a six-byte negative vector at `-6(a6)` containing `JMP $00f80300`;
4. writes **red** (`COLOR00=$F00`) immediately before `JSR -6(a6)`;
5. executes the RAM-resident negative vector through A6;
6. the ROM probe returns `LKV1` (`$4c4b5631`) in D0;
7. stores D0 at `$00001040`;
8. writes **green** (`COLOR00=$0F0`) and enters the final idle loop.

The `-6` vector remains a **LibreKick private probe** and is not claimed as a public Exec LVO.

## Static gate

```sh
make clean
make check
```

PASS requires the expected 512 KiB image, reset vectors, explicit CIAA OVL handoff instructions, Library fields, six-byte negative vector, `lea $2100,a6 ; jsr -6(a6)`, probe routine, red-before/green-after checkpoints, and final ROM checksum `$ffffffff`.

## Runtime gate

```sh
make qualify-m2_1
```

Interpretation on A500/68000:

- **green screen**: OVL handoff succeeded and the RAM vector returned; M2.1b runtime PASS;
- **red screen**: OVL handoff and initialization succeeded, but the negative vector did not return;
- any other stable colour/state: failure occurs before the red checkpoint and requires narrower early-bootstrap diagnosis.

When debugger inspection is available, stronger evidence is `$00000004 == $00002100` and `$00001040 == $4c4b5631` (`LKV1`).

## Non-claims

M2.1b does not yet provide scheduler semantics, memory allocation, signals, messages, interrupts, devices, DOS, Intuition, or a complete public Exec LVO table. It is an ABI-mechanism foundation, not an AmigaOS 3.1-compatible kernel milestone by itself.

## Runtime record

- Date: pending
- Host: pending
- FS-UAE: pending
- CPU/model: A500 / 68000
- Diagnostic screen: pending
- `SysBase`: pending
- `LKV1` result at `$00001040`: pending
- Result: **PENDING**
