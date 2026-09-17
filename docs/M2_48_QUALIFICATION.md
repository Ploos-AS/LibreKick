# M2.48 qualification

Status: **PASS — emulator-qualified**

M2.48 extends the retained M2.47 private CPU context frame into a deterministic private two-task context-switch round trip. The qualification remains deliberately narrower than a public Exec scheduler.

## Qualified source

- Qualified commit: `d9a993a2640c016adf3da3bb7999acdabf858187`
- Generator: `tools/make_m2_48_rom.py`
- Checker: `tools/check_m2_48.py`
- Retained ROM size: 524288 bytes

## Dedicated GitHub Actions qualification

Workflow: `M2.48 runtime qualification`

- Run: `35219753712` (#1) — PASS
- Static job: `105196700442` — PASS
- FS-UAE runtime job: `105196700214` — PASS
- Runtime runner: Ubuntu 24.04

The runtime job completed the FS-UAE execution and uploaded the qualification evidence successfully.

## Evidence artifact

- Artifact: `m2-48-fs-uae-qualification`
- Artifact ID: `10496980583`
- Size: 15165 bytes
- Digest: `sha256:08bfb8390e64905a77e975d18b5d44264e783f0c0265dc361eb906aeeaf77979`
- Expires: 2026-12-16

## Retained profiles

The following retained profiles are promoted to `m2_48` and `emulator-qualified`:

- Amiga 500 (`a500`)
- Amiga 500 Plus (`a500plus`)
- Amiga 600 (`a600`)

Each profile uses `tools/make_m2_48_rom.py` and `tools/check_m2_48.py`, while preserving its model-specific retained ROM artifact.

## Qualification boundary

This qualification proves the M2.48 private deterministic two-task context-switch path under the project emulator qualification environment. It does **not** claim a complete Exec scheduler, task queues, priorities, preemption, interrupt-driven rescheduling, or public `Switch`/`Dispatch`/`Schedule`/`Reschedule` compatibility.
