# A1000.11 Qualification

Status: **EMULATOR QUALIFIED / PASS**

A1000.11 extends the stock-A1000 WCS path with the first private defined CPU-context frame on top of the already-qualified task-pointer and task-stack handoff primitives.

## Qualified revision

- Qualified HEAD: `201468ffe40e60086f94a3d7975399ade5292ce9`
- Machine profile: stock Amiga 1000 WCS architecture
- Bootstrap: A1000.3 DF0 loader
- Retained payload: `build/a1000/librekick-a1000.11-wcs.bin`
- Retained kickdisk: `build/a1000/librekick-a1000.11-kickdisk.adf`

The A1000 runtime workflow explicitly boots the A1000.3 DF0 loader with the A1000.11 private CPU-context WCS payload and retains both the WCS payload and kickdisk as runtime evidence.

## CPU-context slice

A1000.11 introduces a private context frame that preserves and restores:

- SR
- D2-D7
- A2-A6

This builds on the existing private task identity and stack-handoff machinery. The runtime probe verifies that the prepared replacement context executes and that the original context is restored before the success diagnostic is reached.

This is intentionally an internal LibreKick ABI slice. It is a stepping stone toward broader Exec-compatible task switching, not a claim that the public Exec scheduler ABI is implemented.

## GitHub Actions qualification

The qualified revision completed the GitHub-hosted FS-UAE runtime gate successfully:

- Workflow: `FS-UAE runtime qualification`
- Run ID: `35135718961`
- Run number: `350`
- Job: `fs-uae-runtime`
- Job ID: `104927462285`
- Runner: Ubuntu 24.04
- Result: `success`

The runtime job completed all relevant stages successfully, including software OpenGL/Xvfb setup, execution of the current LibreKick ROM in FS-UAE, and upload of runtime evidence.

Runtime evidence artifact:

- Artifact ID: `10463375736`
- Name: `fs-uae-runtime-qualification`
- Size: `10527` bytes
- Digest: `sha256:68e50b025f71e8b804488bd683325c7d2bfa80f9c01f0f5b6b08a96d5cc68c06`
- Created: `2026-09-16T18:45:47Z`

The other workflows triggered for the qualified HEAD also completed successfully, including static qualification.

## Scope

A1000.11 qualifies the private CPU-context-frame mechanism under FS-UAE on the stock-A1000 WCS path. It does **not** claim:

- a public Exec `Switch`, `Dispatch`, `Schedule`, or `Reschedule` implementation;
- public Exec negative-vector compatibility for the new context primitive;
- scheduler-driven task selection;
- complete public `Task` ABI compatibility;
- complete `exec.library` compatibility;
- interrupt/preemption-driven switching;
- real Amiga 1000 hardware qualification.

The next convergence milestone is M2.47: bring the same private CPU-context-frame semantics into the retained 512 KiB ROM profiles and qualify them across the normal profile/runtime matrix.
