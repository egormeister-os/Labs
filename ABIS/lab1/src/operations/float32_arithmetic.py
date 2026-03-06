from core.bit_array32 import BitArray32


class IEEE754Float32Arithmetic:
    """IEEE-754-2008 single-precision arithmetic over bit arrays."""

    def add(self, left: BitArray32, right: BitArray32) -> BitArray32:
        raise NotImplementedError

    def subtract(self, left: BitArray32, right: BitArray32) -> BitArray32:
        raise NotImplementedError

    def multiply(self, left: BitArray32, right: BitArray32) -> BitArray32:
        raise NotImplementedError

    def divide(self, left: BitArray32, right: BitArray32) -> BitArray32:
        raise NotImplementedError
