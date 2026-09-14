# LibreKick M2.37 qualification

M2.37 qualifies a **controlled A7 stack handoff primitive** for the currently selected task.

## Scope

The internal helper follows `ExecBase->ThisTask`, reads classic `Task.tc_SPReg` at offset `+$36`, saves the caller A7, temporarily loads the task stack pointer into A7, performs a real predecrement stack write on that task stack, records the resulting A7, restores the caller A7, and returns safely.

This is deliberately narrower than a real Exec task context switch. M2.37 does **not** save/restore the task register set, SR/CCR, PC, exception frame, or scheduler state and is not exposed as `Switch()`, `Dispatch()`, `Schedule()`, or `Reschedule()`.

## Runtime assertions

The probe executes the helper twice with two different `tc_SPReg` values. Each pass verifies:

- `ExecBase->ThisTask` remains the selected task.
- A7 is loaded from that task's `tc_SPReg`.
- the marker `0x4c4b3737` is written at `tc_SPReg - 4` by a real `MOVE.L #marker,-(A7)` operation.
- the observed switched A7 equals `tc_SPReg - 4`.
- `tc_SPReg` itself is not modified by this bounded helper.
- control returns to the qualification probe, proving caller A7 was restored before `RTS`.

## Final qualification evidence

- implementation HEAD: `3940c932883bf51ffcf2f9403e9ad1055ace1bc2`
- FS-UAE runtime qualification: run `34797984735`, job `103834713562`
- static qualification: run `34797984725`
- ROM size: `524288` bytes
- ROM checksum: `0xffffffff`
- runtime gate: **PASS**
- green ratio: `0.8911`
- blue ratio: `0.0000`
- red ratio: `0.0000`
- dominant RGB: `0,240,0`
- dominant ratio: `0.8901`
- artifact ID: `10330576903`
- artifact size: `9121` bytes
- artifact ZIP SHA-256: `dc16d5bf79b08d167dce488db81e963d758756ccec66fa12df9e1649d0d7c241`

## Verdict

**PASS** for the bounded M2.37 controlled A7 stack-handoff semantics described above.

This result must not be cited as qualification of full Amiga Exec task switching.