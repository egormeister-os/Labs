"""Police department management module."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .Policeman import Policeman
    from .Crime import Crime


class PoliceError(Exception):
    """Base exception for police-related errors."""
    pass


class ZoneNotFoundError(PoliceError):
    """Raised when a zone is not found."""
    pass


class PolicemanNotFoundError(PoliceError):
    """Raised when a policeman is not found."""
    pass


class Police:
    """Represents a police department managing zones and officers."""

    def __init__(self, zones: dict[str, dict] | None = None) -> None:
        self._zones: dict[str, dict] = zones or {}

    @property
    def zones(self) -> dict[str, dict]:
        """Return all zones."""
        return self._zones

    @zones.setter
    def zones(self, value: dict[str, dict]) -> None:
        """Set all zones."""
        self._zones = value

    def create_zone(self, zone: str) -> None:
        """Create a new zone with default values."""
        zone_key = str(zone)
        if zone_key in self._zones:
            raise PoliceError(f"Zone '{zone}' already exists")
        self._zones[zone_key] = {"policemen": [], "security": 1.0}

    def add_zone(self, new_zone: str) -> None:
        """Add a new zone (alias for create_zone)."""
        self.create_zone(new_zone)

    def has_zone(self, zone: str) -> bool:
        """Check if a zone exists."""
        return str(zone) in self._zones

    def hire(self, policeman: Policeman, zone: str) -> None:
        """Hire a policeman to a specific zone."""
        zone_key = str(zone)
        if zone_key not in self._zones:
            raise ZoneNotFoundError(f"Zone '{zone}' does not exist")
        self._zones[zone_key]["policemen"].append(policeman)
        policeman.zone = zone_key

    def fire(self, policeman: Policeman) -> None:
        """Fire a policeman from the police department."""
        zone_key = policeman.zone
        if zone_key not in self._zones:
            raise ZoneNotFoundError(f"Zone '{zone_key}' does not exist")
        if policeman not in self._zones[zone_key]["policemen"]:
            raise PolicemanNotFoundError(f"Policeman '{policeman.lastname}' not found in zone '{zone_key}'")
        self._zones[zone_key]["policemen"].remove(policeman)
        policeman.is_work = False

    def relocate(self, relocated_policemen: list[Policeman], target_zone: str) -> None:
        """Relocate policemen to a new zone."""
        if target_zone not in self._zones:
            raise ZoneNotFoundError(f"Target zone '{target_zone}' does not exist")
        for policeman in relocated_policemen:
            old_zone = str(policeman.zone)
            if old_zone not in self._zones:
                raise ZoneNotFoundError(f"Current zone '{old_zone}' does not exist")
            # Remove from old zone (if present)
            if policeman in self._zones[old_zone]["policemen"]:
                self._zones[old_zone]["policemen"].remove(policeman)
            # Set new zone and add to target
            policeman.zone = target_zone
            # Avoid duplicates - check if already in target zone
            if policeman not in self._zones[target_zone]["policemen"]:
                self._zones[target_zone]["policemen"].append(policeman)

    def get_policemen(self) -> list[Policeman]:
        """Get all policemen from all zones."""
        all_policemen: list[Policeman] = []
        for zone_data in self._zones.values():
            all_policemen.extend(zone_data["policemen"])
        return all_policemen

    def get_policemen_by_zone(self, zone: str) -> list[Policeman]:
        """Get all policemen from a specific zone."""
        if zone not in self._zones:
            raise ZoneNotFoundError(f"Zone '{zone}' does not exist")
        return self._zones[zone]["policemen"].copy()

    def get_crimes_by_zone(self, zone: str, all_crimes: list[Crime]) -> list[Crime]:
        """Get all crimes for a specific zone from the applications list."""
        return [c for c in all_crimes if c.zone == zone]

    def get_all_crimes(self, applications: list[Crime]) -> list[Crime]:
        """Get all crimes from applications."""
        return applications.copy()

    def update_zone_security(self, zone: str, citizen_count: int, crime_count: int) -> None:
        """Update security level for a specific zone."""
        if zone not in self._zones:
            raise ZoneNotFoundError(f"Zone '{zone}' does not exist")
        if crime_count == 0:
            self._zones[zone]["security"] = 10.0
        elif citizen_count == 0:
            self._zones[zone]["security"] = 0.0
        else:
            # Security = citizens in this zone / crimes in this zone
            # Capped at 10.0 for display consistency
            security = citizen_count / crime_count
            self._zones[zone]["security"] = min(10.0, round(security, 2))

    def update_all_zones_security(self, citizens_by_zone: dict[str, int], crimes_by_zone: dict[str, int]) -> None:
        """Update security levels for all zones.
        
        Args:
            citizens_by_zone: Dictionary mapping zone names to citizen counts.
            crimes_by_zone: Dictionary mapping zone names to crime counts.
        """
        for zone in self._zones:
            citizen_count = citizens_by_zone.get(zone, 0)
            crime_count = crimes_by_zone.get(zone, 0)
            self.update_zone_security(zone, citizen_count, crime_count)

    def __repr__(self) -> str:
        return f"Police(zones={list(self._zones.keys())})"
