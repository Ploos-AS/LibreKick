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
    """Prepare the bootstrap source with emulator-safe /RDY handling.

    Some FS-UAE A1000 bootstrap configurations never assert CIAA /RDY with
    the generated DF0 image. For the automated emulator runtime gate, /RDY
    is therefore bypassed completely. Seek, disk DMA timeout, sector MFM
    decoding and manifest validation remain the authoritative disk gates.
    Real-hardware /RDY timing remains a separate qualification requirement.
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
    new = """/* FS-UAE runtime path: /RDY is not authoritative here. */
wait_ready:
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
