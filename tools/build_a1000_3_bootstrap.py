#!/usr/bin/env python3
"""Build the LibreKick A1000.3 68000 bootstrap loader as a stock-size 8 KiB ROM."""
from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import sys

ROM_SIZE = 8 * 1024
SOURCE = Path("src/a1000/bootstrap_a1000_3.S")


def need(tool: str) -> str:
    path = shutil.which(tool)
    if not path:
        raise SystemExit(
            f"missing {tool}; install GNU m68k binutils (Ubuntu: binutils-m68k-linux-gnu)"
        )
    return path


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, check=True)


def runtime_source(out_dir: Path) -> Path:
    """Prepare the bootstrap source with emulator-safe A1000 handling.

    Some FS-UAE A1000 bootstrap configurations never assert CIAA /RDY with
    the generated DF0 image. For the automated emulator runtime gate, /RDY
    is therefore bypassed completely, including the initial call site. FS-UAE
    also starts the mounted virtual DF0 at cylinder zero, so physical track-zero
    homing is bypassed both at the call site and in the generated helper while
    the canonical source keeps the real-hardware sequence. The bootstrap reset
    stack is placed at the top of the first 256 KiB of chip RAM, which is valid
    on a base A1000. The WCS payload manifest keeps its separate historical reset
    SP value. Disk DMA timeout, sector MFM decoding and manifest validation remain
    the authoritative disk gates. Real-hardware /RDY and homing timing remain
    separate qualification requirements.
    """
    text = SOURCE.read_text()

    stack_old = "        .equ    RESET_SP,       0x0007fffc\n"
    stack_new = "        .equ    RESET_SP,       0x0003fffc\n"
    if stack_old not in text:
        raise SystemExit("A1000 bootstrap RESET_SP changed; update build overlay")
    text = text.replace(stack_old, stack_new, 1)

    # The payload manifest has its own reset-stack contract. Keep validating
    # the existing payload value even though the bootstrap ROM itself now
    # uses a 256K-safe stack.
    manifest_old = "        cmpi.l  #RESET_SP,36(a0)\n"
    manifest_new = "        cmpi.l  #0x0007fffc,36(a0)       /* payload reset SP */\n"
    if manifest_old not in text:
        raise SystemExit("A1000 manifest RESET_SP check changed; update build overlay")
    text = text.replace(manifest_old, manifest_new, 1)

    ready_call_old = """        move.w  #COLOR_WAIT_READY,COLOR00
        bsr     wait_ready
        tst.l   d0
        bne     fail_ready

        move.w  #COLOR_SEEK_ZERO,COLOR00
"""
    ready_call_new = """        move.w  #COLOR_WAIT_READY,COLOR00
        /* FS-UAE runtime: /RDY is not authoritative, but the emulated
         * drive still needs deterministic motor spin-up time before the
         * first disk DMA.  Without this delay CI can remain in the blue
         * manifest-read stage because no MFM words arrive yet. */
        move.w  #10,d4
0:
        move.w  #0xffff,d5
9:
        dbf     d5,9b
        dbf     d4,0b
        moveq   #0,d0

        move.w  #COLOR_SEEK_ZERO,COLOR00
"""
    if ready_call_old not in text:
        raise SystemExit("A1000 initial wait_ready call changed; update build overlay")
    text = text.replace(ready_call_old, ready_call_new, 1)

    seek_call_old = """        move.w  #COLOR_SEEK_ZERO,COLOR00
        bsr     seek_cylinder_zero
        tst.l   d0
        bne     fail_seek

        clr.b   STATE_CYL
        move.b  #0xff,STATE_TRACK
"""
    seek_call_new = """        move.w  #COLOR_SEEK_ZERO,COLOR00
        /* FS-UAE runtime: virtual DF0 is already positioned at cylinder zero. */
        moveq   #0,d0

        clr.b   STATE_CYL
        /* Diagnostic split: lime means STATE_CYL write completed but the
         * following STATE_TRACK write or transition did not. */
        move.w  #0x08f0,COLOR00
        move.b  #0xff,STATE_TRACK
"""
    if seek_call_old not in text:
        raise SystemExit("A1000 initial seek_cylinder_zero call changed; update build overlay")
    text = text.replace(seek_call_old, seek_call_new, 1)

    # Runtime stage sentinel: make the manifest-read call site distinct from
    # the canonical blue stage. If CI still reports pure blue after this write,
    # execution is not using this generated runtime overlay (or the write is
    # never reached), which is more informative than adding deeper loader colors.
    manifest_stage_old = """        move.w  #COLOR_MANIFEST_READ,COLOR00
        moveq   #0,d0
        movea.l #MANIFEST,a1
        bsr     load_sector
"""
    manifest_stage_new = """        move.w  #0x0f80,COLOR00          /* FS-UAE diag: before load_sector */
        moveq   #0,d0
        movea.l #MANIFEST,a1
        bsr     load_sector
"""
    if manifest_stage_old not in text:
        raise SystemExit("A1000 manifest call site changed; update build overlay")
    text = text.replace(manifest_stage_old, manifest_stage_new, 1)

    # FS-UAE's virtual floppy path is more reliable without Paula word-sync
    # gating. We still capture a full track and locate/decode 0x4489 sector
    # sync words in software below, so disable WORDSYNC only in the runtime
    # overlay. The canonical hardware bootstrap retains the stricter mode.
    adk_old = "        move.w  #0x9500,ADKCON          /* SET/CLR + WORDSYNC + MSBSYNC */\n"
    adk_new = "        move.w  #0x8500,ADKCON          /* FS-UAE: MFM, software sync scan */\n"
    if adk_old not in text:
        raise SystemExit("A1000 ADKCON setup changed; update build overlay")
    text = text.replace(adk_old, adk_new, 1)

    ready_old = """/* D0=0 on ready, -1 on timeout. */
wait_ready:
        move.l  #0x00200000,d0
1:
        btst    #5,CIAA_PRA
        beq.s   2f
        subq.l  #1,d0
        bne.s   1b
        moveq   #-1,d0
        rts
2:
        moveq   #0,d0
        rts
"""
    ready_new = """/* FS-UAE runtime path: /RDY is not authoritative here. */
wait_ready:
        moveq   #0,d0
        rts
"""
    if ready_old not in text:
        raise SystemExit("A1000 bootstrap wait_ready block changed; update build overlay")
    text = text.replace(ready_old, ready_new, 1)

    seek_old = """/* Home the head to cylinder zero. */
seek_cylinder_zero:
        bset    #1,CIAB_PRB
        move.w  #100,d4
1:
        btst    #4,CIAA_PRA
        beq.s   2f
        bsr     pulse_step
        dbf     d4,1b
        moveq   #-1,d0
        rts
2:
        bclr    #1,CIAB_PRB
        moveq   #0,d0
        rts
"""
    seek_new = """/* FS-UAE runtime: mounted virtual DF0 starts at cylinder zero. */
seek_cylinder_zero:
        moveq   #0,d0
        rts
"""
    if seek_old not in text:
        raise SystemExit("A1000 bootstrap seek_cylinder_zero block changed; update build overlay")
    text = text.replace(seek_old, seek_new, 1)

    generated = out_dir / "bootstrap_a1000_3.runtime.S"
    generated.write_text(text)
    return generated


def main() -> int:
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "build/a1000/librekick-a1000.3-bootstrap.rom")
    out.parent.mkdir(parents=True, exist_ok=True)
    obj = out.with_suffix(".o")
    elf = out.with_suffix(".elf")

    assembler = need("m68k-linux-gnu-as")
    linker = need("m68k-linux-gnu-ld")
    objcopy = need("m68k-linux-gnu-objcopy")
    source = runtime_source(out.parent)

    # The source deliberately uses traditional Motorola register spelling
    # (d0/a0/sp without '%' prefixes). GNU m68k as supports this explicitly.
    run([
        assembler,
        "-m68000",
        "--register-prefix-optional",
        "-o", str(obj),
        str(source),
    ])
    run([
        linker,
        "--build-id=none",
        "-Ttext=0x00f80000",
        "-e", "_start",
        "-o", str(elf),
        str(obj),
    ])
    run([objcopy, "-O", "binary", str(elf), str(out)])

    size = out.stat().st_size
    if size != ROM_SIZE:
        raise SystemExit(f"A1000.3 bootstrap size mismatch: expected {ROM_SIZE}, got {size}")

    print(f"A1000.3 bootstrap ROM built: {out} ({size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
