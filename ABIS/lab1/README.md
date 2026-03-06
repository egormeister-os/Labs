# Lab 1 (OOP Structure)

## Student
- Full name: `<your name>`
- Group: `<your group>`
- Variant: `D (Excess-3 BCD)`

## Goal
Build a bit-level calculator for representations and arithmetic over fixed 32-bit arrays (`0/1`) using an object-oriented architecture.

## Architecture layers
- `core` - domain primitives and shared interfaces.
- `converters` - representation codecs (sign-magnitude, ones', two's complement).
- `operations` - arithmetic engines (integer, float32, Excess-3 BCD).
- `services` - facade that coordinates codecs and operations.
- `ui` - CLI adapter (ready for replacing with GUI later).

## Project tree
```text
lab1/
├─ run.py
├─ src/
│  ├─ core/
│  │  ├─ bit_array32.py
│  │  └─ interfaces.py
│  ├─ converters/
│  │  ├─ decimal_binary.py
│  │  ├─ sign_magnitude.py
│  │  ├─ ones_complement.py
│  │  └─ twos_complement.py
│  ├─ operations/
│  │  ├─ integer_arithmetic.py
│  │  ├─ float32_arithmetic.py
│  │  └─ bcd_excess3_arithmetic.py
│  ├─ services/
│  │  └─ lab_service.py
│  └─ ui/
│     ├─ cli.py
│     └─ formatter.py
├─ tests/
│  ├─ core/
│  ├─ converters/
│  ├─ operations/
│  ├─ services/
│  └─ ui/
└─ report/
   ├─ theory.md
   ├─ examples.md
   └─ screenshots/
```

## Run
```bash
python run.py
```

## Import and launch rules
- The project uses package-style imports: `from src....`.
- Run the app from project root.
- Internal files are modules, not standalone scripts.

Examples:
```bash
python run.py
python -m src.converters.sign_magnitude
```

## Notes
- Current files are scaffolds with class/method stubs (`NotImplementedError`).
- Implement logic gradually and cover with tests.
