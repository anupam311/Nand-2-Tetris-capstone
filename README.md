# Nand2Tetris Capstone "Make the Computer Draw a Box"

**Personal number K:** 51  
**Box:** 64 pixels wide Ã— 20 rows high, starting at screen row 51.  
**Assembler extra feature:** Export labels and variables to `symbols.txt`; warn on duplicate labels.

## Project contents

- `capstone/CPU.hdl`  Hack CPU
- `capstone/Memory.hdl`  RAM, Screen and Keyboard memory map
- `capstone/Computer.hdl`  complete Hack computer
- `capstone/assembler.py`  two-pass Python assembler
- `capstone/Box.asm`  personalized keyboard-controlled rectangle
- `capstone/Box.hack`  assembled machine code
- `capstone/symbols.txt`  labels and variables from the assembler
- `tests/`  official test materials and assembler examples
- `screenshots/`  evidence for the report
- `report/`  assignment report

## Assemble the box program

From the repository root:

```powershell
py -3.12 .\capstone\assembler.py .\capstone\Box.asm .\capstone\Box.hack
```

## Hardware testing

Open the Nand2Tetris Hardware Simulator, load each HDL chip, and run the matching Project 5 test script in `tests/official`.

Test `Memory.hdl` with `Memory.tst`, and `CPU.hdl` with `CPU.tst`. Then load `Computer.hdl` and run the ComputerAdd, ComputerMax and ComputerRect tests.

Use the CPU Emulator to load `Box.hack` and interact with the keyboard.

**Important:** The PowerShell setup script creates the source files and downloads test materials. It does not itself run the Nand2Tetris HDL simulators.