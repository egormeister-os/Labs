"""Policeman module representing law enforcement officers."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .Crime import Crime


class Policeman:
    """Represents a police officer who can arrest criminals and investigate crimes."""

    def __init__(
        self,
        lastname: str,
        zone: str | int | float,
        is_work: bool = True
    ) -> None:
        # Validate lastname on initialization
        if not isinstance(lastname, str):
            raise TypeError("Lastname must be a string")
        if not lastname.strip():
            raise ValueError("Lastname cannot be empty")
        if len(lastname.strip()) < 2:
            raise ValueError("Lastname must contain at least 2 characters")

        self._lastname: str = lastname
        self._zone: str | int | float = zone
        self._is_work: bool = is_work
        self._fatigue: int = 0
        self._criminal: tuple[Crime, int] | None = None
        self._is_resting: bool = False  # Track if officer is on rest

    @property
    def zone(self) -> str | int | float:
        """Return the officer's zone."""
        return self._zone

    @zone.setter
    def zone(self, value: str | int | float) -> None:
        """Set the officer's zone."""
        self._zone = value

    @property
    def lastname(self) -> str:
        """Return the officer's lastname."""
        return self._lastname

    @lastname.setter
    def lastname(self, value: str) -> None:
        """Set the officer's lastname with validation."""
        if not isinstance(value, str):
            raise TypeError("Lastname must be a string")
        if not value.strip():
            raise ValueError("Lastname cannot be empty")
        if len(value.strip()) < 2:
            raise ValueError("Lastname must contain at least 2 characters")
        self._lastname = value.strip()

    @property
    def is_work(self) -> bool:
        """Return whether the officer is on duty."""
        return self._is_work

    @is_work.setter
    def is_work(self, value: bool) -> None:
        """Set the officer's work status."""
        self._is_work = value

    @property
    def fatigue(self) -> int:
        """Return the officer's fatigue level."""
        return self._fatigue

    def arrest(self) -> bool:
        """
        Attempt to arrest the assigned criminal.

        Returns:
            bool: True if arrest was successful, False otherwise.
        """
        if not self._criminal:
            return False

        crime, severity = self._criminal
        # Higher fatigue and severity reduce success chance
        success_chance = 1 - (self._fatigue + severity) / 20
        success_chance = max(0.1, min(0.9, success_chance))  # Clamp between 0.1 and 0.9

        arrested = random.random() < success_chance

        if arrested:
            self._criminal = None

        self._fatigue += 1
        
        # Check if officer is now exhausted
        self.check_exhaustion()
        
        return arrested

    def assign_crime(self, criminal: tuple[Crime, int]) -> None:
        """Assign a crime-criminal tuple to the officer for arrest."""
        self._criminal = criminal

    @property
    def has_assignment(self) -> bool:
        """Check if the officer has an assigned criminal."""
        return self._criminal is not None

    @property
    def assignment(self) -> tuple[Crime, int] | None:
        """Return current assignment tuple (crime, severity) if present."""
        return self._criminal

    @property
    def is_resting(self) -> bool:
        """Check if the officer is currently resting due to exhaustion."""
        return self._is_resting

    def recovery(self) -> None:
        """Reset officer's fatigue to zero and return from rest."""
        self._fatigue = 0
        self._is_resting = False

    def check_exhaustion(self) -> bool:
        """
        Check if officer is exhausted and should go on rest.

        Returns:
            bool: True if officer is exhausted (fatigue >= 6).
        """
        if self._fatigue >= 6:
            self._is_resting = True
            return True
        return False

    def clear_assignment(self) -> None:
        """Clear the officer's current assignment."""
        self._criminal = None

    def __repr__(self) -> str:
        status = "on duty" if self._is_work else "off duty"
        if self._is_resting:
            fatigue_icon = "⏸️ Resting"
        elif self._fatigue < 3:
            fatigue_icon = "🟢 Fresh"
        elif self._fatigue < 6:
            fatigue_icon = "🟡 Tired"
        else:
            fatigue_icon = "🔴 Exhausted"
        return (
            f"Policeman(lastname={self._lastname!r}, zone={self._zone!r}, "
            f"{status}, fatigue={fatigue_icon})"
        )

    def __str__(self) -> str:
        rest_status = " [RESTING]" if self._is_resting else ""
        return f"Officer {self._lastname} (Zone: {self._zone}){rest_status}"
