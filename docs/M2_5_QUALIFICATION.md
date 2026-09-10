# M2.5 Exec Queue/Search Qualification

Status: **PASS**

M2.5 completes the classic Exec list/queue slice by adding the two public functions that follow the M2.4 primitives:

- `Enqueue(list,node)` at **-270(a6)** — A0/A1
- `FindName(start,name)` at **-276(a6)** — A0/A1, result in D0/Z

M2.5 retains the already-qualified Insert/AddHead/AddTail/Remove/RemHead/RemTail vectors.

## Runtime semantic probe

The ROM creates three full Nodes with priorities and names and enqueues them in this order:

1. node1: priority 10, name `alpha`
2. node2: priority 5, name `beta`
3. node3: priority 10, name `alpha`

Expected queue order is `node1 -> node3 -> node2`: higher priority first, while equal-priority nodes remain FIFO.

The probe then verifies `FindName` semantics:

- `FindName(list,"alpha")` returns node1;
- `FindName(node1,"alpha")` skips node1 and returns node3;
- `FindName(node3,"alpha")` returns NULL;
- `FindName(list,"beta")` returns node2;
- `FindName(list,"missing")` returns NULL.

Diagnostic colours:

- **red** (`$F00`) = probe running / a call failed to return;
- **yellow** (`$FF0`) = Enqueue ordering validated; FindName probe running;
- **blue** (`$00F`) = a call returned but semantic validation failed;
- **green** (`$0F0`) = complete M2.5 semantic PASS.

## Static gate

```sh
make clean
make check
```

The static gate verifies ROM size/reset vectors, OVL handoff, Library V40.5 header, negative vector space through -276, all eight classic list/queue LVO slots, three Enqueue calls, five FindName calls, Enqueue delegation through Insert, the 68000 illegal-address-register `TST` regression guard, corrected 68000 Bcc.W/BRA.W PC-relative branch base, test strings, PASS/FAIL markers and the final one's-complement checksum.

## Runtime gate

```sh
make qualify-m2_5
```

Target: FS-UAE A500 / 68000. Runtime PASS requires a stable green screen and clean emulator operation until manual exit.

## Qualification notes

During runtime qualification, an early M2.5 build consistently stopped inside the first `Enqueue()` call. Incremental colour checkpoints localized the failure to the word-sized conditional branch immediately after the empty-list sentinel read. The generator's generic `patch_branch()` helper was using `target - (pos + 4)` for Bcc.W/BRA.W displacement. On 68000 the PC-relative base for these instructions is the branch opcode address plus 2, so the generated branch destination was two bytes early. Correcting the helper to use `target - (pos + 2)` fixed both the Enqueue and FindName word branches. The subsequent A500/68000 runtime probe reached the stable green PASS marker.

## Non-claims

M2.5 does not yet implement memory allocation, task scheduling, signals, messages, interrupts, devices, DOS, Intuition or a complete `ExecBase` ABI.

## Runtime record

- Date: 2026-09-10
- Host: Linux x86-64
- FS-UAE: 3.2.35
- CPU/model: A500 / 68000
- ROM size: 524288 bytes
- FS-UAE ROM identifier: `8eb858c2`
- Static check: **PASS** — `Exec Enqueue(-270)/FindName(-276); corrected 68000 Bcc.W PC base; checksum=0xffffffff`
- Diagnostic screen: stable green (`$0F0`)
- Emulator exit: normal/manual (`UAE: Calling uae_quit` / `UAE: Stopping`)
- Result: **PASS**
