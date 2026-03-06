from core.bit_array32 import BitArray32
from core.interfaces import IntegerCodec


class OnesComplementCodec(IntegerCodec):
    """Ones' complement integer representation codec."""

    def encode(self, value: int) -> BitArray32:
        raise NotImplementedError

    def decode(self, bits: BitArray32) -> int:
        raise NotImplementedError
