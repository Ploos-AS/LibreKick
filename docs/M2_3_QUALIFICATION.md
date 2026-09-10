# M2.3 Public Exec List Primitive Qualification

Status: **PASS**

M2.3 extends LibreKick's public `exec.library` slice with two documented list primitives:

- `AddHead(List *list, Node *node)` at LVO **-240(a6)** with `list` in A0 and `node` in A1;
- `RemHead(List *list)` at LVO **-258(a6)** with `list` in A0 and the removed `Node *` (or NULL) returned in D0.

M2.3 does not yet claim the complete Exec list API or full ExecBase compatibility.

## Runtime probe

The ROM performs a self-contained semantic probe in Chip RAM:

1. disables OVL correctly so low memory is RAM;
2. initializes a canonical empty Amiga `List` sentinel layout at `$00001100`;
3. initializes a probe `Node` at `$00001120`;
4. calls `AddHead` through public LVO -240;
5. calls `RemHead` through public LVO -258 and requires D0 to equal `$00001120`;
6. verifies the list has returned to its empty sentinel state;
7. calls `RemHead` again and requires D0 == NULL;
8. writes green to `COLOR00` only if all checks pass.

Diagnostic colours:

- **green** (`$0F0`) = AddHead/RemHead semantic probe PASS;
- **blue** (`$00F`) = LVO calls returned but list semantics/result validation failed;
- **red** (`$F00`) = probe entered but did not reach a completed validation path.

## Static gate

```sh
make clean
make check
```

Static PASS verifies the 512 KiB ROM, reset vectors, OVL handoff, Library V40.3 header, negative-vector reach through -258, exact public call offsets, exact 68000 routine bytes, runtime markers, routine non-overlap, and final one's-complement ROM checksum.

Observed static qualification output:

```text
M2.3 check PASS: build/librekick-m2_3.rom (524288 bytes)
Exec AddHead(-240)/RemHead(-258); one-node + empty-list probe; checksum=0xffffffff
```

## Runtime gate

```sh
make qualify-m2_3
```

Target: FS-UAE A500 / 68000. Runtime PASS requires a stable green screen and clean emulator operation until manual exit.

Observed runtime result: **PASS**. The stable green screen was observed, and FS-UAE ran until normal manual exit without a reset loop or emulator-side failure.

## Non-claims

M2.3 does not yet implement `Insert`, `AddTail`, `Remove`, `RemTail`, `Enqueue`, `FindName`, memory allocation, scheduling, signals, messages, interrupts, devices, DOS, or Intuition.

## Runtime record

- Date: 2026-09-10
- FS-UAE: 3.2.35 (Linux x86-64)
- CPU/model: A500 / 68000
- ROM size: 524288 bytes
- FS-UAE ROM identifier: `aa3e6c6f`
- Static checksum: `0xffffffff`
- Diagnostic screen: stable green (`COLOR00=$0F0`) observed
- Emulator exit: normal manual exit (`UAE: Calling uae_quit` / `UAE: Stopping`)
- Result: **PASS**
