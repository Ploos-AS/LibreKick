# LibreKick M2.40 qualification

M2.40 qualifies a narrow **SR-aware task context frame** on the current/bootstrap task stack.

## Qualified scope

The private M2.40 helper temporarily hands A7 to `ThisTask->tc_SPReg`, captures the complete 16-bit 68000 SR, saves SR plus the already-qualified preserved-register subset `D2-D7/A2-A6` on the task stack, deliberately perturbs only CCR bits, restores the preserved registers, then restores the captured SR as the final context operation before returning to the caller stack.

The runtime probe verifies the selected task remains `ExecBase->ThisTask`, the task stack frame is placed at the expected address, every preserved register is restored to its original value, and the zero-extended SR captured before the perturbation exactly matches the SR observed after restoration.

## Important limitation

This is **not** a complete task switch and is not a public `Switch()`, `Dispatch()`, `Schedule()` or `Reschedule()` implementation. M2.40 does not capture a resumable PC, does not transfer execution to another task, does not save the complete volatile register set, and does not claim compatibility with the classic Exec scheduler/context-frame layout. The frame is a private LibreKick qualification primitive.

## Runtime evidence

- Qualified HEAD: `03f3b1e074406b32187db7100ab0daf2f1ddd43a`
- FS-UAE runtime qualification: run `34798770597` (#161), success
- Static qualification: run `34798770624` (#287), success
- ROM size: 524288 bytes
- ROM ones-complement checksum: `0xffffffff`
- Runtime color gate: PASS (green diagnostic screen)
- Runtime artifact ID: `10331000598`
- Artifact size: 9121 bytes
- Artifact ZIP SHA-256: `fec8a2d426d96eb858f08f2adcc9e3eb96520069a65671a0d73519d04ed2cd60`

## Result

**M2.40 PASS** for the bounded SR-aware context-frame semantics above. This result must not be interpreted as qualification of a complete Exec task context switch.
