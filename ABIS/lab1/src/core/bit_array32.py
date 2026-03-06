from __future__ import annotations


class BitArray32:
    """Mutable 32-bit container used as the canonical internal representation."""

    SIZE = 32

    def __init__(self, bits: list[int] | None = None) -> None:
        if bits is None:
            self._bits = [0] * self.SIZE
            return
        if len(bits) != self.SIZE or any(bit not in (0, 1) for bit in bits):
            raise ValueError("BitArray32 expects exactly 32 bits (0/1).")
        self._bits = bits[:]

    @property
    def bits(self) -> list[int]:
        return self._bits

    def copy(self) -> "BitArray32":
        return BitArray32(self._bits)

    def __getitem__(self, idx: int) -> int:
        return self._bits[idx]

    def __setitem__(self, idx: int, value: int) -> None:
        if value not in (0, 1):
            raise ValueError("Bit value must be 0 or 1.")
        self._bits[idx] = value

    def __len__(self) -> int:
        return self.SIZE

    def __iter__(self):
        return iter(self._bits)

    def __str__(self) -> str:
        return "".join(str(bit) for bit in self._bits)
