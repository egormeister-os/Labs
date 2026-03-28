"""Crime module representing criminal offenses."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .Citizen import Citizen
    from .Law import Law


class Crime:
    """Represents a criminal offense with suspect, description, and applicable law."""

    def __init__(
        self,
        suspect: Citizen,
        description: str,
        zone: str,
        law: Law
    ) -> None:
        self.description: str = description
        self.suspect: Citizen = suspect
        self.zone: str = zone
        self.law: Law = law

    @property
    def severity(self) -> int:
        """Return the severity level of the crime based on the law."""
        return self.law.severity

    def __repr__(self) -> str:
        return (
            f"Crime(description={self.description!r}, "
            f"suspect={self.suspect!r}, zone={self.zone!r}, law={self.law!r})"
        )

    def __str__(self) -> str:
        return f"Crime: {self.description} (Zone: {self.zone}, Severity: {self.severity})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Crime):
            return NotImplemented
        return (
            self.description == other.description
            and self.suspect == other.suspect
            and self.zone == other.zone
            and self.law == other.law
        )

    def __hash__(self) -> int:
        return hash((self.description, self.suspect, self.zone, self.law))
