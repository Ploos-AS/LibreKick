# M2.4 Basic Exec List API Qualification

Status: **STATIC READY / RUNTIME PENDING**

M2.4 completes the basic doubly-linked `exec.library` list primitive slice around the already-qualified M2.3 functions.

Public LVOs covered:

- `Insert(list,node,pred)` at **-234(a6)** — A0/A1/A2
- `AddHead(list,node)` at **-240(a6)** — A0/A1
- `AddTail(list,node)` at **-246(a6)** — A0/A1
- `Remove(node)` at **-252(a6)** — A1
- `RemHead(list)` at **-258(a6)** — A0, result in D0
- `RemTail(list)` at **-264(a6)** — A0, result in D0

The offsets and register ABI follow the published Exec function table/autodocs. M2.4 does not yet include `Enqueue` or `FindName`.

## Runtime semantic probe

The ROM disables OVL, creates a canonical empty Amiga `List` and three Nodes in Chip RAM, then exercises the public LVOs through A6:

1. `AddTail(node1)` and `AddTail(node2)`;
2. `Insert(node3, pred=node1)`, expecting order node1 -> node3 -> node2;
3. validates head, tail predecessor, successor and predecessor links;
4. `Remove(node3)`, expecting node1 -> node2;
5. `RemTail()` returns node2, then node1, then NULL on the empty list;
6. validates canonical empty-list sentinels;
7. separately calls `Insert(node3, pred=NULL)` and requires head-insertion semantics;
8. uses the already-qualified `RemHead()` to remove it and verifies NULL on the now-empty list.

Diagnostic colours:

- **green** (`$0F0`) = all semantic checks passed;
- **blue** (`$00F`) = a call returned but a list/result assertion failed;
- **red** (`$F00`) = probe entered but did not reach a completed validation path.

## Static gate

```sh
make clean
make check
```

Static PASS verifies the 512 KiB ROM, reset vectors, OVL handoff, Library V40.4 header, negative vector space through -264, the six exact public vector targets and routine bodies, multi-node probe call sites, no routine overlap, success/failure markers, and final one's-complement checksum `$ffffffff`.

## Runtime gate

```sh
make qualify-m2_4
```

Target: FS-UAE A500 / 68000. Runtime PASS requires a stable green screen and clean emulator operation until manual exit.

## Non-claims

M2.4 does not yet implement `Enqueue`, `FindName`, memory allocation, task scheduling, signals, messages, interrupts, devices, DOS, Intuition, or a complete `ExecBase` ABI.

## Runtime record

- Date: pending
- Host: pending
- FS-UAE: pending
- CPU/model: A500 / 68000
- ROM identifier/hash: pending
- Diagnostic screen: pending
- Result: **PENDING**
