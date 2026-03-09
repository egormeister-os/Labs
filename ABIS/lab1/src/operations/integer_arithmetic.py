from src.core.bit_array32 import BitArray32

class TwosComplementArithmetic:
    """Addition and subtraction in two's complement."""

    def add(self, left: BitArray32, right: BitArray32) -> BitArray32:
        result_bits = BitArray32()
        carry = 0

        for bit_idx in range(left.SIZE - 1, -1, -1):
            bit_sum = left[bit_idx] + right[bit_idx] + carry
            result_bits[bit_idx] = bit_sum % 2
            carry = bit_sum // 2

        return result_bits

    def subtract(self, left: BitArray32, right: BitArray32) -> BitArray32:
        """Implement as left + (-right)."""
        right.invert()
        right.add_one()

        result_bits = self.add(left, right)
        return result_bits


class SignMagnitudeArithmetic:
    """Multiplication and division in sign-magnitude representation."""

    def multiply(self, left: BitArray32, right: BitArray32) -> BitArray32:
        raise NotImplementedError

    def divide(self, left: BitArray32, right: BitArray32, precision: int = 5) -> tuple[BitArray32, float]:
        raise NotImplementedError
