"""Investigation module for analyzing crimes and identifying suspects."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .Crime import Crime
    from .Citizen import Citizen


class Investigation:
    """
    Conducts investigations on crimes to identify guilty parties.
    
    The investigation uses probability based on crime severity to
    determine if a suspect is found guilty.
    """

    def __init__(self, crimes: list[Crime]) -> None:
        self._crimes: list[Crime] = crimes

    @property
    def crimes(self) -> list[Crime]:
        """Return the list of crimes under investigation."""
        return self._crimes

    def investigate(self) -> tuple[Crime, int] | None:
        """
        Investigate crimes and determine guilt.
        
        Returns:
            A tuple of (crime, severity) if guilt is determined, None otherwise.
        """
        for crime in self._crimes:
            # Higher severity = higher chance of guilt being detected
            guilt_chance = crime.severity / 5.0
            guilt = random.random() < guilt_chance
            
            if guilt:
                return (crime, crime.law.severity)
        
        return None

    def investigate_all(self) -> list[tuple[Crime, int]]:
        """
        Investigate all crimes and return all guilty findings.
        
        Returns:
            List of tuples (crime, severity) for each guilty finding.
        """
        results: list[tuple[Crime, int]] = []
        for crime in self._crimes:
            guilt_chance = crime.severity / 5.0
            if random.random() < guilt_chance:
                results.append((crime, crime.law.severity))
        return results

    def __repr__(self) -> str:
        return f"Investigation(crimes={len(self._crimes)})"
