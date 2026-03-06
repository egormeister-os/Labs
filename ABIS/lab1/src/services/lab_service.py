from converters.ones_complement import OnesComplementCodec
from converters.sign_magnitude import SignMagnitudeCodec
from converters.twos_complement import TwosComplementCodec
from operations.bcd_excess3_arithmetic import Excess3BCDArithmetic
from operations.float32_arithmetic import IEEE754Float32Arithmetic
from operations.integer_arithmetic import SignMagnitudeArithmetic, TwosComplementArithmetic


class LabService:
    """Facade for all lab tasks."""

    def __init__(self) -> None:
        self.sign_magnitude_codec = SignMagnitudeCodec()
        self.ones_codec = OnesComplementCodec()
        self.twos_codec = TwosComplementCodec()
        self.twos_ops = TwosComplementArithmetic()
        self.sign_ops = SignMagnitudeArithmetic()
        self.float_ops = IEEE754Float32Arithmetic()
        self.excess3_ops = Excess3BCDArithmetic()
