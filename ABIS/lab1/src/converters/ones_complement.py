from src.core.bit_array32 import BitArray32
from src.converters.decimal_binary import DecimalBinaryConverter
from src.core.interfaces import IntegerCodec


class OnesComplementCodec(IntegerCodec):
    """Ones' complement integer representation codec."""

    def encode(self, value: int) -> BitArray32:
        pass


    def decode(self, bits: BitArray32) -> int:
        pass
