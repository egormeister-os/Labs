from core.bit_array32 import BitArray32


class OutputFormatter:
    """Responsible only for rendering operation results."""

    def bits_and_decimal(self, bits: BitArray32, decimal_value: int | float) -> str:
        return f"Binary: {bits}\nDecimal: {decimal_value}"
