from src.converters.ones_complement import OnesComplementCodec
from src.converters.sign_magnitude import SignMagnitudeCodec
from src.converters.twos_complement import TwosComplementCodec
from src.operations.bcd_excess3_arithmetic import Excess3BCDArithmetic
from src.operations.float32_arithmetic import IEEE754Float32Arithmetic
from src.operations.integer_arithmetic import SignMagnitudeArithmetic, TwosComplementArithmetic


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
