# Lab 1: Binary Representations and Arithmetic (32-bit bit arrays)

## Student
- Full name: `Mukhamedzianav Egor`
- Group: `421701`
- Variant: `D (Excess-3 BCD)`

## Goal
Implement number representations and arithmetic operations manually on 32-bit arrays of `0/1` without built-in conversion helpers.

## Required tasks
- Decimal -> binary in sign-magnitude, ones' complement, and two's complement.
- Add 2 integers in two's complement.
- Subtract via `A + (-B)` in two's complement.
- Multiply 2 integers in sign-magnitude.
- Divide 2 integers in sign-magnitude with precision up to 5 fractional digits.
- Add/subtract/multiply/divide two IEEE-754-2008 float32 values.
- Add two numbers in BCD (variant D: Excess-3).
- For every operation, print both binary and decimal output.

## Constraints
Do **not** use language/library features that directly perform:
- decimal <-> binary conversion (`bin`, `format(..., 'b')`, `int(x, 2)`, etc.),
- decimal <-> float-bit packing (`struct`, etc.),
- ready-made IEEE-754 or BCD utilities.

All internal data must be stored and processed as arrays of `0/1` with size `32`.

## Project structure
- `run.py` - entry point / CLI orchestration.
- `src/bit_array.py` - shared bit-array helpers.
- `src/conversions/*` - integer representation conversions.
- `src/integer_ops/*` - integer arithmetic operations.
- `src/float32/*` - IEEE-754 float32 operations.
- `src/bcd/*` - Excess-3 encoding and addition.
- `src/io/*` - input parsing and output formatting.
- `tests/*` - test cases.
- `report/*` - theory + examples for submission.

## How to run
```bash
python run.py
```

## Completion checklist
- [ ] Decimal -> sign-magnitude
- [ ] Decimal -> ones' complement
- [ ] Decimal -> two's complement
- [ ] Two's complement addition
- [ ] Two's complement subtraction via `A + (-B)`
- [ ] Sign-magnitude multiplication
- [ ] Sign-magnitude division (5-digit precision)
- [ ] IEEE-754 float32: +, -, *, /
- [ ] Excess-3 BCD addition
- [ ] Binary + decimal output for all operations

## Notes
Document overflow handling, divide-by-zero handling, normalization rules for float32, and any assumptions in `report/theory.md`.
