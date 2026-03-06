from core.bit_array32 import BitArray32
from core.interfaces import IntegerCodec


class SignMagnitudeCodec(IntegerCodec):
    """Sign-magnitude integer representation codec."""

    def encode(self, value: int) -> BitArray32:
        raise NotImplementedError

    def decode(self, bits: BitArray32) -> int:
        raise NotImplementedError
