"""Security module for evaluating public safety levels."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .Crime import Crime
    from .Citizen import Citizen


class Security:
    """Evaluates and tracks the security level of an area."""

    def __init__(self, base_level: float = 1.0) -> None:
        self._level: float = base_level

    @property
    def level(self) -> float:
        """Return the current security level."""
        return self._level

    @level.setter
    def level(self, value: float) -> None:
        """Set the security level."""
        if value < 0:
            raise ValueError("Security level cannot be negative")
        self._level = value

    def eval(self, citizens: list[Citizen], crimes: list[Crime]) -> float:
        """
        Evaluate security level based on citizen-to-crime ratio.
        
        Args:
            citizens: List of citizens in the area.
            crimes: List of crimes committed.
            
        Returns:
            float: Security level (higher is safer).
        """
        if not crimes:
            self._level = 10.0  # Maximum security when no crimes
            return self._level
        
        if len(citizens) == 0:
            self._level = 0.0
            return self._level
            
        self._level = len(citizens) / len(crimes)
        return self._level

    def decrease(self, amount: float = 0.1) -> None:
        """Decrease security level by a given amount."""
        self._level = max(0.0, self._level - amount)

    def increase(self, amount: float = 0.1) -> None:
        """Increase security level by a given amount."""
        self._level += amount

    def __repr__(self) -> str:
        return f"Security(level={self._level:.2f})"

    def __str__(self) -> str:
        status = "High" if self._level >= 5 else "Medium" if self._level >= 2 else "Low"
        return f"Security Level: {status} ({self._level:.2f})"
