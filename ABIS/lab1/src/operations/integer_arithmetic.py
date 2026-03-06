from src.core.bit_array32 import BitArray32


class TwosComplementArithmetic:
    """Addition and subtraction in two's complement."""

    def add(self, left: BitArray32, right: BitArray32) -> BitArray32:
        raise NotImplementedError

    def subtract(self, left: BitArray32, right: BitArray32) -> BitArray32:
        """Implement as left + (-right)."""
        raise NotImplementedError


class SignMagnitudeArithmetic:
    """Multiplication and division in sign-magnitude representation."""

    def multiply(self, left: BitArray32, right: BitArray32) -> BitArray32:
        raise NotImplementedError

    def divide(self, left: BitArray32, right: BitArray32, precision: int = 5) -> tuple[BitArray32, float]:
        raise NotImplementedError
