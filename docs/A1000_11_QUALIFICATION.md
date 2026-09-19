# A1000.11 Qualification

Status: **HISTORICAL STATIC/IMPLEMENTATION RECORD — dedicated stock-A1000 runtime qualification not established**

A1000.11 extends the stock-A1000 WCS path with the first private defined CPU-context frame on top of the already-qualified task-pointer and task-stack handoff primitives.

## Qualified revision

- Qualified HEAD: `201468ffe40e60086f94a3d7975399ade5292ce9`
- Machine profile: stock Amiga 1000 WCS architecture
- Bootstrap: A1000.3 DF0 loader
- Retained payload: `build/a1000/librekick-a1000.11-wcs.bin`
- Retained kickdisk: `build/a1000/librekick-a1000.11-kickdisk.adf`

A1000.11 implemented the private CPU-context WCS payload on top of the A1000.3 DF0-loader architecture. The historical evidence retained below is useful implementation evidence, but it does not establish that the dedicated stock-A1000 bootstrap/WCS runtime workflow executed A1000.11 successfully.

## CPU-context slice

A1000.11 introduces a private context frame that preserves and restores:

- SR
- D2-D7
- A2-A6

This builds on the existing private task identity and stack-handoff machinery. The runtime probe verifies that the prepared replacement context executes and that the original context is restored before the success diagnostic is reached.

This is intentionally an internal LibreKick ABI slice. It is a stepping stone toward broader Exec-compatible task switching, not a claim that the public Exec scheduler ABI is implemented.

## Historical GitHub Actions evidence

The earlier version of this document incorrectly treated generic FS-UAE runtime run `35135718961` (job `104927462285`, artifact `10463375736`) as dedicated A1000.11 qualification evidence. That run belongs to the generic 512 KiB ROM runtime path and therefore cannot prove execution of the stock-A1000 bootstrap → Kickdisk → WCS path.

A dedicated A1000.11 runtime PASS has not been established from the retained evidence. Consequently A1000.11 should not independently be described as emulator-qualified.

This historical evidence gap does not affect the later A1000.12 qualification: A1000.12 was independently qualified through the dedicated stock-A1000 bootstrap runtime workflow, including the 8 KiB bootstrap ROM, DF0 Kickdisk, 256 KiB WCS load and terminal green runtime gate. See `docs/A1000_12_QUALIFICATION.md`.

## Scope

A1000.11 records the private CPU-context-frame implementation intended for the stock-A1000 WCS path; dedicated runtime qualification is not claimed. It does **not** claim:

- a public Exec `Switch`, `Dispatch`, `Schedule`, or `Reschedule` implementation;
- public Exec negative-vector compatibility for the new context primitive;
- scheduler-driven task selection;
- complete public `Task` ABI compatibility;
- complete `exec.library` compatibility;
- interrupt/preemption-driven switching;
- real Amiga 1000 hardware qualification.

The next convergence milestone is M2.47: bring the same private CPU-context-frame semantics into the retained 512 KiB ROM profiles and qualify them across the normal profile/runtime matrix.
