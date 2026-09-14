# LibreKick M2.42 qualification

M2.42 qualifies an **integrated private register/SR/PC context-transfer slice**. It combines the previously-qualified preserved-register frame (`D2-D7`, `A2-A6`), SR save/restore, task-stack A7 handoff, and private PC resume transfer in one current-task round trip.

This is deliberately **not** a claim of full Exec `Switch()`, `Dispatch()`, `Schedule()` or `Reschedule()` compatibility. It does not yet perform scheduler-driven task-to-task switching or save a complete outgoing task context.

## Qualified build

- HEAD: `1cc7c36509a7cc1c94ffbd80a1f745c9ef84b2d9`
- FS-UAE runtime qualification: run `34821514831` (#173), job `103903933369` — PASS
- Static qualification: run `34821514717` (#299) — PASS
- ROM size: 524288 bytes
- ROM checksum: `0xffffffff`

## Runtime evidence

The runtime probe reached the green PASS gate in FS-UAE:

- `green_ratio=0.8911`
- `blue_ratio=0.0000`
- `red_ratio=0.0000`
- dominant RGB: `0,240,0`
- dominant ratio: `0.8901`

Runtime artifact:

- artifact ID: `10338019349`
- size: 9120 bytes
- ZIP SHA-256: `a5063c259f56f49c4c2b899c739334fcfefad5d975e6a814ba5e996b62d2fd8f`

## Semantics proved by the probe

The private handoff captures the entry SR, redirects A7 to `ThisTask->tc_SPReg`, pushes the SR and preserved register subset on the task stack, deliberately perturbs those registers/CCR, pushes a private resume PC, and transfers execution through `RTS`. The resume path restores `A2-A6`, `D2-D7`, restores SR last, restores the caller stack and returns through the saved caller PC.

The probe verifies the task-stack frame topology, resume PC, current task pointer, restored register observations, and equality of the entry/returned SR values before entering the green gate.

## Explicit limitations

M2.42 is a private current-task round trip only. It does not yet save a complete outgoing task context, restore a different task, perform ready/wait scheduling, implement preemption, or expose public Exec scheduler vectors.