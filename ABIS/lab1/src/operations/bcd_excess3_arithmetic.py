class Excess3BCDArithmetic:
    """Variant D: Excess-3 BCD operations."""

    def encode_number(self, value: int) -> list[list[int]]:
        raise NotImplementedError

    def add(self, left: int, right: int) -> tuple[list[list[int]], int]:
        raise NotImplementedError
