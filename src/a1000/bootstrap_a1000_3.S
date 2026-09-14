/* LibreKick A1000.3 clean-room bootstrap -> DF0 -> WCS loader.
 *
 * This is a deliberately small 68000-only bootstrap. It reads standard
 * Amiga MFM sectors from DF0 through Paula disk DMA, validates the private
 * A1000.2 manifest, copies exactly 256 KiB to the A1000 WCS window at
 * $FC0000, switches out the bootstrap mapping from a chip-RAM trampoline,
 * and transfers control to the payload entry at $FC0008.
 *
 * The low-level sector layout and DMA sequence are based on public Amiga
 * hardware documentation and independently cross-checked against public-
 * domain Amiga floppy test code. No Commodore bootstrap ROM code is used.
 */

        .cpu    68000
        .section .text

        .equ    RESET_SP,       0x0007fffc
        .equ    BOOT_BASE,      0x00f80000
        .equ    WCS_BASE,       0x00fc0000
        .equ    WCS_ENTRY,      0x00fc0008

        .equ    COLOR00,        0x00dff180
        .equ    CIAB_PRB,       0x00bfd100
        .equ    CIAB_DDRB,      0x00bfd300
        .equ    CIAA_PRA,       0x00bfe001

        .equ    DSKPTH,         0x00dff020
        .equ    DSKLEN,         0x00dff024
        .equ    INTREQR_LO,     0x00dff01f
        .equ    DSKSYNC,        0x00dff07e
        .equ    DMACON,         0x00dff096
        .equ    INTREQ,         0x00dff09c
        .equ    ADKCON,         0x00dff09e

        .equ    MFM_BUFFER,     0x00010000
        .equ    MANIFEST,       0x00014000
        .equ    TRAMPOLINE,     0x00015000
        .equ    STATE_TRACK,    0x00015f00
        .equ    STATE_CYL,      0x00015f01
        .equ    STATE_RETRY,    0x00015f02

        .equ    MFM_BYTES,      0x3200
        .equ    MFM_WORDS,      0x1900
        .equ    SECTOR_MFM,     0x0438
        .equ    MASK_MFM,       0x55555555

        /* A1000.3 runtime diagnostic palette.  These are intentionally
         * vivid and distinct so a headless CI screenshot identifies the
         * exact stage reached even when the loader blocks instead of
         * returning through a failure path.
         *
         *   yellow   = bootstrap entered
         *   orange   = waiting for DF0 ready
         *   cyan     = homing/seek cylinder zero
         *   blue     = reading manifest sector
         *   magenta  = validating manifest
         *   violet   = loading 256 KiB payload
         *   white    = WCS handoff trampoline
         *   green    = WCS payload itself (A1000.2 payload)
         */
        .equ    COLOR_BOOT,             0x0ff0
        .equ    COLOR_WAIT_READY,       0x0f80
        .equ    COLOR_SEEK_ZERO,        0x00ff
        .equ    COLOR_MANIFEST_READ,    0x000f
        .equ    COLOR_MANIFEST_CHECK,   0x0f0f
        .equ    COLOR_PAYLOAD_LOAD,     0x080f
        .equ    COLOR_WCS_HANDOFF,      0x0fff

        /* Distinct terminal failure colors. */
        .equ    FAIL_READY_COLOR,       0x0f00
        .equ    FAIL_SEEK_COLOR,        0x0f40
        .equ    FAIL_MANIFEST_COLOR,    0x0f08
        .equ    FAIL_VALIDATE_COLOR,    0x0f0f
        .equ    FAIL_PAYLOAD_COLOR,     0x080f

        .globl  _start
_start:
        .long   RESET_SP
        .long   reset

reset:
        move.w  #0x2700,sr
        move.w  #COLOR_BOOT,COLOR00

        /* CIAB port B drives motor/select/side/direction/step. */
        move.b  #0xff,CIAB_DDRB
        /* DF0 selected, motor on, side 0, direction outward, STEP high. */
        move.b  #0x77,CIAB_PRB

        move.w  #COLOR_WAIT_READY,COLOR00
        bsr     wait_ready
        tst.l   d0
        bne     fail_ready

        move.w  #COLOR_SEEK_ZERO,COLOR00
        bsr     seek_cylinder_zero
        tst.l   d0
        bne     fail_seek

        clr.b   STATE_CYL
        move.b  #0xff,STATE_TRACK

        /* Read and validate sector-0 LibreKick-private manifest. */
        move.w  #COLOR_MANIFEST_READ,COLOR00
        moveq   #0,d0
        movea.l #MANIFEST,a1
        bsr     load_sector
        tst.l   d0
        bne     fail_manifest

        move.w  #COLOR_MANIFEST_CHECK,COLOR00
        movea.l #MANIFEST,a0
        cmpi.l  #0x4c494252,0(a0)       /* LIBR */
        bne     fail_validate
        cmpi.l  #0x454b4943,4(a0)       /* EKIC */
        bne     fail_validate
        cmpi.l  #0x4b2d4131,8(a0)       /* K-A1 */
        bne     fail_validate
        cmpi.l  #0x30303000,12(a0)      /* 000\0 */
        bne     fail_validate
        cmpi.l  #2,16(a0)               /* format version */
        bne     fail_validate
        cmpi.l  #512,20(a0)             /* payload file offset */
        bne     fail_validate
        cmpi.l  #0x00040000,24(a0)      /* 256 KiB */
        bne     fail_validate
        cmpi.l  #WCS_BASE,28(a0)
        bne     fail_validate
        cmpi.l  #WCS_ENTRY,32(a0)
        bne     fail_validate
        cmpi.l  #RESET_SP,36(a0)
        bne     fail_validate

        /* Sectors 1..512 are exactly the 256 KiB WCS payload. */
        move.w  #COLOR_PAYLOAD_LOAD,COLOR00
        movea.l #WCS_BASE,a1
        moveq   #1,d6
        move.w  #511,d7
payload_loop:
        move.l  d6,d0
        bsr     load_sector
        tst.l   d0
        bne     fail_payload
        addq.l  #1,d6
        dbf     d7,payload_loop

        /* Execute the WCS lock/switch sequence from chip RAM so the mapping
         * can change underneath us safely before the final jump to WCS. */
        move.w  #COLOR_WCS_HANDOFF,COLOR00
        lea     lock_trampoline(pc),a0
        movea.l #TRAMPOLINE,a1
        move.w  #(lock_trampoline_end-lock_trampoline)/2-1,d0
copy_trampoline:
        move.w  (a0)+,(a1)+
        dbf     d0,copy_trampoline
        jmp     TRAMPOLINE

fail_ready:
        move.w  #FAIL_READY_COLOR,COLOR00
        bra.s   fail_hang
fail_seek:
        move.w  #FAIL_SEEK_COLOR,COLOR00
        bra.s   fail_hang
fail_manifest:
        move.w  #FAIL_MANIFEST_COLOR,COLOR00
        bra.s   fail_hang
fail_validate:
        move.w  #FAIL_VALIDATE_COLOR,COLOR00
        bra.s   fail_hang
fail_payload:
        move.w  #FAIL_PAYLOAD_COLOR,COLOR00
fail_hang:
        bra.s   fail_hang

/* D0=0 on ready, -1 on timeout. */
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

/* Home the head to cylinder zero. */
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

pulse_step:
        bclr    #0,CIAB_PRB
        bsr     step_delay
        bset    #0,CIAB_PRB
        bsr     step_delay
        rts

step_delay:
        move.w  #12000,d5
1:
        dbf     d5,1b
        rts

/* D0 = logical ADF sector number, A1 = destination. A1 advances 512 bytes.
 * Returns D0=0 on success, -1 after bounded retries.
 */
load_sector:
        movem.l d1-d7/a0/a2-a5,-(sp)
        movea.l a1,a5
        move.b  #3,STATE_RETRY

        move.l  d0,d2
        divu.w  #11,d2                  /* quotient=track, remainder=sector */
        move.l  d2,d4
        swap    d4                      /* d4.w = sector */
        andi.l  #0x0000ffff,d2          /* d2.w = track */

        cmp.b   STATE_TRACK,d2
        beq     decode_cached

        /* Select side from track bit zero. */
        btst    #0,d2
        bne.s   side_one
        bset    #2,CIAB_PRB
        bra.s   side_done
side_one:
        bclr    #2,CIAB_PRB
side_done:
        /* Sequential loader: move inward until target cylinder is reached. */
        move.w  d2,d1
        lsr.w   #1,d1
        moveq   #0,d3
        move.b  STATE_CYL,d3
seek_inward_loop:
        cmp.w   d1,d3
        bcc.s   seek_done
        bclr    #1,CIAB_PRB
        bsr     pulse_step
        addq.w  #1,d3
        move.b  d3,STATE_CYL
        bra.s   seek_inward_loop
seek_done:
        bsr     wait_ready
        tst.l   d0
        bne     load_fail_final

read_retry:
        movea.l a5,a1
        movea.l #MFM_BUFFER,a4

        move.l  a4,DSKPTH
        move.w  #0x8210,DMACON          /* set DMA master + disk DMA */
        move.w  #0x0002,INTREQ          /* clear DSKBLK */
        move.w  #0x7f00,ADKCON          /* clear disk control bits */
        move.w  #0x9500,ADKCON          /* MFM + word sync */
        move.w  #0x4489,DSKSYNC
        move.w  #0x9900,DSKLEN
        move.w  #0x9900,DSKLEN          /* disk DMA requires double write */

        move.l  #0x00a00000,d1
wait_dma:
        btst    #1,INTREQR_LO
        bne.s   dma_done
        subq.l  #1,d1
        bne.s   wait_dma
        bra     retry_sector
dma_done:
        move.w  #0x4000,DSKLEN
        move.b  d2,STATE_TRACK

decode_cached:
        movea.l a5,a1
        movea.l #MFM_BUFFER,a4
        lea     MFM_BYTES-SECTOR_MFM(a4),a2
        move.l  #MASK_MFM,d5
find_sync:
        cmpa.l  a4,a2
        bmi     retry_sector
        cmpi.w  #0x4489,(a4)+
        bne.s   find_sync
        cmpi.w  #0x4489,(a4)
        beq.s   find_sync

        movem.l (a4),d2-d3
        bsr     decode_mfm_long
        lsr.w   #8,d2                   /* d2.w = decoded sector */
        cmp.w   d4,d2
        beq.s   sector_found
        lea     SECTOR_MFM(a4),a4
        bra.s   find_sync

sector_found:
        swap    d2                      /* d2.b = decoded track */
        cmp.b   STATE_TRACK,d2
        bne     retry_sector
        lea     0x30(a4),a4
        move.l  (a4)+,d4
        move.l  (a4)+,d3
        eor.l   d3,d4
        moveq   #0x7f,d7
copy_data_long:
        move.l  0x200(a4),d3
        move.l  (a4)+,d2
        eor.l   d2,d4
        eor.l   d3,d4
        bsr     decode_mfm_long
        move.l  d2,(a1)+
        dbf     d7,copy_data_long
        and.l   d5,d4
        bne     retry_sector

        moveq   #0,d0
        movem.l (sp)+,d1-d7/a0/a2-a5
        rts

retry_sector:
        move.w  #0x4000,DSKLEN
        movea.l a5,a1
        subq.b  #1,STATE_RETRY
        bne     read_retry
load_fail_final:
        moveq   #-1,d0
        movem.l (sp)+,d1-d7/a0/a2-a5
        rts

/* d2 = MFM odd long, d3 = MFM even long. */
decode_mfm_long:
        and.l   d5,d2
        and.l   d5,d3
        add.l   d2,d2
        or.l    d3,d2
        rts

        .align  2
lock_trampoline:
        /* In A1000 bootstrap mode, a write to the lower kick-memory half
         * switches out bootstrap mapping / write-protects the populated WCS.
         * Running this tiny sequence from chip RAM avoids self-unmapping. */
        move.b  #0,BOOT_BASE
        jmp     WCS_ENTRY
lock_trampoline_end:

        .align  4
bootstrap_marker:
        .ascii  "LIBREKICK-A1000.3\0DF0-WCS-LOADER\0"
        .ascii  "DIAG:YEL=BOOT,ORG=READY,CYN=SEEK,BLU=MANIFEST,MAG=CHECK,VIO=PAYLOAD,WHT=HANDOFF,GRN=WCS\0"

        /* A1000 bootstrap container is retained as exactly 64 KiB. */
        .org    0x10000,0xff
