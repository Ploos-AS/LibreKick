# LibreKick M2.38 Qualification

## Scope

M2.38 qualifies a **bounded small register-context frame primitive** on the selected task stack.

The qualified slice:

- follows `ExecBase->ThisTask`,
- reads classic `Task.tc_SPReg` at `+$36`,
- temporarily hands A7 to that task stack,
- saves D2 and A2 on the task stack,
- deliberately clobbers both registers,
- restores A2 and D2 from the task stack,
- records the restored values for the runtime probe,
- restores the caller A7 and returns safely,
- repeats the operation with an independent stack/register set.

This is **not** a complete task context switch and must not be described as one. M2.38 does not save/restore SR or PC, does not preserve the full 68000 register file, and does not transfer execution from one task to another. It also does not expose `Switch()` or `Dispatch()` semantics.

## Qualified implementation

Final implementation HEAD:

`34c2610e70e334da2af9ceea404f2b0969effde7`

ROM marker:

`LIBREKICK-M2.38\0EXEC-CONTEXT-REGFRAME\0`

Ident:

`exec.library\0LibreKick M2.38 small register-context frame slice 40.38\0`

The runtime frame uses D2 then A2 pushes, giving an 8-byte frame below the starting `tc_SPReg`. The probe verifies both frame contents and the restored register observations.

## Static qualification

GitHub Actions workflow:

- workflow: `M1 static qualification`
- run number: **#277**
- run ID: `34798226540`
- result: **PASS**

The current ROM generator and checker complete successfully and preserve the 512 KiB ROM/checksum contract.

## FS-UAE runtime qualification

GitHub Actions workflow:

- workflow: `FS-UAE runtime qualification`
- run number: **#151**
- run ID: `34798226546`
- job ID: `103835417858`
- result: **PASS**
- HEAD: `34c2610e70e334da2af9ceea404f2b0969effde7`

Runtime evidence:

- ROM size: `524288` bytes
- checker: `M2.38 check PASS`
- ROM checksum: `0xffffffff`
- screenshot: `960x540`
- green ratio: `0.8911`
- blue ratio: `0.0000`
- red ratio: `0.0000`
- dominant RGB: `0,240,0`
- dominant ratio: `0.8901`
- runtime verdict: `FS-UAE runtime gate PASS: green diagnostic screen`

Artifact:

- artifact ID: `10329769456`
- artifact size: `9120` bytes
- ZIP SHA-256: `cf021a28aedaf78449e3870b2d0afce1b7d6c105f175762ea7b44dd7f6dfc4b1`

## Verdict

**M2.38 PASS.**

The qualified claim is deliberately narrow: LibreKick can save and restore a small D2/A2 register frame using the current task's stack while safely restoring the caller stack. Full task context switching remains future work.
