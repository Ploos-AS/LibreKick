#!/usr/bin/env python3
"""Build the LibreKick A1000.3 68000 bootstrap loader as a 64 KiB ROM."""
from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import sys

ROM_SIZE = 64 * 1024
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
    """Prepare the bootstrap source with emulator-safe advisory /RDY handling.

    Some FS-UAE A1000 bootstrap configurations do not assert CIAA /RDY even
    with a mounted DF0 image. /RDY is therefore treated as a short spin-up
    hint only; seek, DMA timeout and MFM validation remain authoritative.
    Real-hardware /RDY timing stays a separate qualification requirement.
    """
    text = SOURCE.read_text()
    old = """/* D0=0 on ready, -1 on timeout. */
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
    new = """/* /RDY is advisory here: sample it for a short bounded interval,
 * then continue. Seek, disk DMA timeout and MFM validation remain
 * authoritative, including on emulators that never assert /RDY. */
wait_ready:
        move.w  #0x1000,d0
1:
        btst    #5,CIAA_PRA
        beq.s   2f
        subq.w  #1,d0
        bne.s   1b
2:
        moveq   #0,d0
        rts
"""
    if old not in text:
        raise SystemExit("A1000 bootstrap wait_ready block changed; update build overlay")
    generated = out_dir / "bootstrap_a1000_3.runtime.S"
    generated.write_text(text.replace(old, new, 1))
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
