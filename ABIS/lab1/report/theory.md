# Theory Notes (Template)

## 1. 32-bit storage model
- How bits are stored (indexing convention, MSB/LSB choice).
- Why fixed 32-bit arrays are used.

## 2. Integer representations
### 2.1 Sign-magnitude
- Sign bit semantics.
- Magnitude layout.
- Range and edge cases.

### 2.2 Ones' complement
- Rule for positive values.
- Rule for negative values (bit inversion).
- Existence of +0 and -0.

### 2.3 Two's complement
- Rule for positive values.
- Rule for negative values (invert + add 1).
- Why addition/subtraction is convenient.

## 3. Integer arithmetic
### 3.1 Addition in two's complement
- Bitwise sum with carry.
- Overflow detection rule.

### 3.2 Subtraction via addition
- Identity: `A - B = A + (-B)`.
- How `-B` is formed in two's complement.

### 3.3 Multiplication in sign-magnitude
- Sign computation.
- Magnitude multiplication by shift-and-add.

### 3.4 Division in sign-magnitude
- Sign computation.
- Magnitude long division.
- Fractional part to 5 digits: method used.
- Divide-by-zero behavior.

## 4. IEEE-754 float32
- Layout: 1 sign bit, 8 exponent bits (bias 127), 23 fraction bits.
- Normalized value formula.
- Denormals / zero / infinity / NaN handling strategy.
- Operation pipeline for +, -, *, /:
  - unpack,
  - align/operate,
  - normalize,
  - round,
  - pack.

## 5. BCD (Variant D: Excess-3)
- Digit encoding rule: `digit -> digit + 3` in 4 bits.
- Multi-digit addition process.
- Correction rules per tetrad and carry handling.

## 6. Validation strategy
- Which edge cases are tested.
- How binary and decimal outputs are cross-checked.
