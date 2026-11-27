// Capstone box program  K = 51
// Top row = 51; height = 20 rows; width = 64 pixels (4 words).
// SCREEN base = 16384 + (51 * 32) = 18016.
// A pressed key draws black; no key clears the same rectangle.

(LOOP)
    @KBD
    D=M
    @SET_BLACK
    D;JGT

    @COLOR
    M=0
    @DRAW
    0;JMP

(SET_BLACK)
    @COLOR
    M=-1

(DRAW)
    // PTR = SCREEN + 51*32
    @18016
    D=A
    @PTR
    M=D

    // ROWS = 20
    @20
    D=A
    @ROWS
    M=D

(ROW_LOOP)
    // Four 16-bit words = 64 pixels.
    @4
    D=A
    @COLS
    M=D

(COL_LOOP)
    @COLOR
    D=M
    @PTR
    A=M
    M=D

    @PTR
    M=M+1

    @COLS
    M=M-1
    D=M
    @COL_LOOP
    D;JGT

    // Move from the end of this 4-word segment to the next
    // screen row: +28 more words (4 already advanced).
    @28
    D=A
    @PTR
    M=D+M

    @ROWS
    M=M-1
    D=M
    @ROW_LOOP
    D;JGT

    @LOOP
    0;JMP