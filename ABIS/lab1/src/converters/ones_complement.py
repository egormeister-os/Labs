from src.core.bit_array32 import BitArray32
from src.converters.sign_magnitude import SignMagnitudeCodec
from src.core.interfaces import IntegerCodec


class OnesComplementCodec(IntegerCodec):
    """Ones' complement integer representation codec."""

    def encode(self, value: int) -> BitArray32:
        converter = SignMagnitudeCodec()

        if value >= 0:
            bits = converter.encode(value)
            return bits
        
        else:
            bits = converter.encode(abs(value))
            for i in range(bits.SIZE):
                bits[i] = 1 - bits[i]

            return bits

    def decode(self, input_bits: BitArray32) -> int:
        converter = SignMagnitudeCodec()
        bits = input_bits.copy()
        
        if bits.bits[0] == 0:
            value = converter.decode(bits)
            return value
        
        else:
            for i in range(1, bits.SIZE):
                bits[i] = 1 - bits[i]

            value = converter.decode(bits)
            return value