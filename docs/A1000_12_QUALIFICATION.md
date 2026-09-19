# LibreKick A1000.12 qualification

Status: **PASS — emulator-qualified**

A1000.12 qualifies the stock-Amiga-1000 boot architecture rather than treating the machine as a generic 512 KiB ROM target.

## Qualified path

The retained path is:

1. 8 KiB LibreKick A1000 bootstrap ROM at `$00F80000`.
2. DF0 LibreKick private Kickdisk container.
3. 256 KiB WCS payload loaded at `$00FC0000`.
4. Transfer to the WCS entry at `$00FC0008`.
5. Shared Exec-compatible state at ExecBase `$00003400`.
6. Private deterministic task A → task B → task A context switch.
7. Restore of SR, D2-D7, A2-A6 and task stack state through `tc_SPReg`.
8. Green diagnostic terminal state.

This remains a private runtime mechanism. It does **not** claim a complete Exec scheduler, ready/wait queues, priorities, preemption, interrupt-driven scheduling, or public Switch/Dispatch/Schedule/Reschedule compatibility.

## GitHub Actions evidence

- Workflow: A1000 bootstrap runtime qualification
- Run: `35435933159`
- Result: **success**
- Runtime artifact: `10582224606`
- Artifact name: `librekick-a1000.12-bootstrap-runtime-qualification`
- Diagnostic: `green_ratio=0.9010`, `blue_ratio=0.0000`, `red_ratio=0.0000`
- Dominant RGB: `0,240,0`
- Runtime gate: `FS-UAE runtime gate PASS: green diagnostic screen`

The same revision also passed the A1000.12 static qualification, A1000 bootstrap static qualification, A1000 Kickdisk static qualification, M1 static qualification, generic FS-UAE runtime qualification and M2.48 runtime qualification.

## Qualification boundary

This is an emulator qualification on the GitHub runner. It establishes the retained LibreKick A1000 bootstrap/WCS execution path in FS-UAE. It is not a claim of qualification on physical Amiga 1000 hardware; real floppy-drive timing, physical media behavior and hardware-specific WCS behavior remain separate qualification targets.
