from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.domain import (
    Citizen,
    Crime,
    Investigation,
    Law,
    Police,
    Policeman,
    PolicemanNotFoundError,
    Security,
    ZoneNotFoundError,
)
from app.storage import PickleStorage


@dataclass(slots=True)
class OperationResult:
    ok: bool
    message: str
    details: list[str] = field(default_factory=list)
    data: Any | None = None


@dataclass(slots=True)
class DashboardState:
    zones_count: int
    policemen_count: int
    citizens_count: int
    crimes_count: int
    laws_count: int
    history_count: int
    overall_security: float
    zones: list[dict[str, Any]] = field(default_factory=list)
    recent_history: list[str] = field(default_factory=list)


class PoliceSystem:
    """Shared application service used by CLI and future web handlers."""

    def __init__(self, storage: PickleStorage | None = None) -> None:
        self.storage = storage or PickleStorage()
        self._load_data()

    def _load_data(self) -> None:
        state = self.storage.load()
        self.police: Police = state["police"]
        self.applications: list[Crime] = state["applications"]
        self.history: list[str] = state["history"]
        self.citizens: list[Citizen] = state["citizens"]
        self.laws: list[Law] = state["laws"]
        self.security: Security = state["security"]

    def save_data(self) -> OperationResult:
        self.storage.save(
            {
                "police": self.police,
                "applications": self.applications,
                "history": self.history,
                "citizens": self.citizens,
                "laws": self.laws,
                "security": self.security,
            }
        )
        return OperationResult(ok=True, message="Data saved successfully")

    def get_dashboard_state(self) -> DashboardState:
        return DashboardState(
            zones_count=len(self.police.zones),
            policemen_count=len(self.police.get_policemen()),
            citizens_count=len(self.citizens),
            crimes_count=len(self.applications),
            laws_count=len(self.laws),
            history_count=len(self.history),
            overall_security=self.security.level,
            zones=self.get_zone_info(),
            recent_history=self.history[-5:],
        )

    def _update_security(self) -> None:
        citizens_by_zone = {zone: 0 for zone in self.police.zones}
        for citizen in self.citizens:
            if citizen.zone and citizen.zone in citizens_by_zone:
                citizens_by_zone[citizen.zone] += 1

        crimes_by_zone = {zone: 0 for zone in self.police.zones}
        for crime in self.applications:
            if crime.zone in crimes_by_zone:
                crimes_by_zone[crime.zone] += 1

        self.police.update_all_zones_security(citizens_by_zone, crimes_by_zone)
        self.security.eval(self.citizens, self.applications)

    def create_statement(
        self,
        description: str,
        zone: str,
        suspect_idx: int,
        law_idx: int,
    ) -> OperationResult:
        if not self.citizens:
            return OperationResult(False, "No citizens registered")
        if not self.laws:
            return OperationResult(False, "No laws defined")
        if not self.police.has_zone(zone):
            return OperationResult(False, f"Zone '{zone}' does not exist")
        if suspect_idx < 0 or law_idx < 0:
            return OperationResult(False, "Invalid citizen or law index")

        try:
            suspect = self.citizens[suspect_idx]
            law = self.laws[law_idx]
        except IndexError:
            return OperationResult(False, "Invalid citizen or law index")

        application = Crime(
            suspect=suspect,
            description=description,
            zone=zone,
            law=law,
        )
        self.applications.append(application)
        self._update_security()
        self.history.append(f"Crime report filed: {application.suspect.name} - {description}")
        return OperationResult(True, "Crime report filed successfully", data=application)

    def delete_statement(self, index: int) -> OperationResult:
        if index < 0:
            return OperationResult(False, "Invalid application index")
        try:
            removed = self.applications.pop(index)
        except IndexError:
            return OperationResult(False, "Invalid application index")

        self._update_security()
        self.history.append(f"Application deleted: {removed.description}")
        return OperationResult(True, "Application deleted", data=removed)

    def list_statements(self) -> list[Crime]:
        return list(self.applications)

    def add_citizen(self, name: str, zone: str | None = None) -> OperationResult:
        if zone is not None and not self.police.has_zone(zone):
            return OperationResult(False, f"Zone '{zone}' does not exist")

        citizen = Citizen(name=name, zone=zone)
        self.citizens.append(citizen)
        self._update_security()
        self.history.append(f"Citizen added: {name}")
        return OperationResult(True, f"Citizen '{name}' added", data=citizen)

    def delete_citizen(self, index: int) -> OperationResult:
        if index < 0:
            return OperationResult(False, "Invalid citizen index")
        try:
            removed = self.citizens.pop(index)
        except IndexError:
            return OperationResult(False, "Invalid citizen index")

        self._update_security()
        self.history.append(f"Citizen removed: {removed.name}")
        return OperationResult(True, "Citizen removed", data=removed)

    def list_citizens(self) -> list[Citizen]:
        return list(self.citizens)

    def hire_policeman(self, lastname: str, zone: str) -> OperationResult:
        if not self.police.has_zone(zone):
            return OperationResult(False, f"Zone '{zone}' does not exist. Create it first.")

        policeman = Policeman(lastname=lastname, zone=zone)
        self.police.hire(policeman=policeman, zone=zone)
        self.history.append(f"Policeman {lastname} hired to zone {zone}")
        return OperationResult(True, f"Officer {lastname} hired to zone {zone}", data=policeman)

    def fire_policeman(self, lastname: str) -> OperationResult:
        for policeman in self.police.get_policemen():
            if policeman.lastname != lastname:
                continue
            try:
                self.police.fire(policeman)
            except (ZoneNotFoundError, PolicemanNotFoundError) as exc:
                return OperationResult(False, f"Error: {exc}")

            self.history.append(f"Policeman {lastname} fired")
            return OperationResult(True, f"Officer {lastname} fired")

        return OperationResult(False, f"Policeman '{lastname}' not found")

    def add_zone(self, zone: str) -> OperationResult:
        try:
            self.police.add_zone(zone)
        except Exception as exc:
            return OperationResult(False, f"Error: {exc}")

        self.history.append(f"Zone '{zone}' created")
        self._update_security()
        return OperationResult(True, f"Zone '{zone}' created")

    def list_policemen(self) -> list[Policeman]:
        return self.police.get_policemen()

    def recover_policemen(self) -> OperationResult:
        recovered = 0
        for officer in self.police.get_policemen():
            if officer.is_resting:
                officer.recovery()
                recovered += 1

        if recovered > 0:
            return OperationResult(True, f"{recovered} officer(s) recovered from rest")
        return OperationResult(True, "No officers need recovery")

    def get_zone_info(self) -> list[dict[str, Any]]:
        zones: list[dict[str, Any]] = []
        for zone_id, data in sorted(self.police.zones.items()):
            officers = []
            for policeman in data["policemen"]:
                if policeman.is_resting:
                    fatigue_status = "Resting"
                elif policeman.fatigue < 3:
                    fatigue_status = "Fresh"
                elif policeman.fatigue < 6:
                    fatigue_status = "Tired"
                else:
                    fatigue_status = "Exhausted"

                officers.append(
                    {
                        "lastname": policeman.lastname,
                        "zone": policeman.zone,
                        "fatigue": policeman.fatigue,
                        "fatigue_status": fatigue_status,
                        "has_assignment": policeman.has_assignment,
                        "is_resting": policeman.is_resting,
                    }
                )

            zone_crimes = [crime for crime in self.applications if crime.zone == zone_id]
            zones.append(
                {
                    "zone": zone_id,
                    "officers": officers,
                    "crimes": zone_crimes,
                    "security": data["security"],
                }
            )
        return zones

    def relocate_policemen(self, indexes: list[int], target_zone: str) -> OperationResult:
        if not self.police.has_zone(target_zone):
            return OperationResult(False, f"Target zone '{target_zone}' does not exist")
        if any(index < 0 for index in indexes):
            return OperationResult(False, "Invalid policeman index")

        policemen = self.police.get_policemen()
        try:
            relocated = [policemen[index] for index in indexes]
            self.police.relocate(relocated_policemen=relocated, target_zone=target_zone)
        except IndexError:
            return OperationResult(False, "Invalid policeman index")
        except (ZoneNotFoundError, PolicemanNotFoundError) as exc:
            return OperationResult(False, f"Error: {exc}")

        self.history.append(f"Policemen relocated to zone {target_zone}")
        moved_names = [officer.lastname for officer in self.police.get_policemen_by_zone(target_zone)]
        return OperationResult(
            True,
            f"Officers relocated to zone {target_zone}",
            details=[f"- {name}" for name in moved_names],
        )

    def investigate_crimes(self, do_arrest: bool = False) -> OperationResult:
        if not self.applications:
            return OperationResult(False, "No crimes to investigate")

        for officer in self.police.get_policemen():
            officer.clear_assignment()

        results = Investigation(self.applications).investigate_all()
        if not results:
            return OperationResult(False, "Investigation inconclusive for all crimes")

        available_officers = [
            officer
            for officer in self.police.get_policemen()
            if not officer.has_assignment and not officer.is_resting
        ]

        details: list[str] = []
        officer_idx = 0
        assigned_count = 0

        for crime, severity in results:
            details.append(f"{crime.suspect.name} is likely guilty")
            details.append(f"Crime: {crime.description}, Severity: {severity}")
            if officer_idx < len(available_officers):
                officer = available_officers[officer_idx]
                officer.assign_crime((crime, severity))
                details.append(f"Assigned to: {officer.lastname} ({officer.zone})")
                officer_idx += 1
                assigned_count += 1
            else:
                details.append("No available officer for assignment")

        if assigned_count == 0:
            details.append("No officers available for arrest assignments")

        message = f"Investigation completed for {len(results)} crime(s)"
        if do_arrest:
            arrest_result = self.arrest_criminals()
            details.extend(arrest_result.details)
            details.append(arrest_result.message)
        return OperationResult(True, message, details=details, data=results)

    def arrest_criminals(self) -> OperationResult:
        officers = self.police.get_policemen()
        arrests = 0
        failed = 0
        solved_crime_ids: set[int] = set()
        details: list[str] = []

        for officer in officers:
            if not officer.has_assignment:
                continue

            assignment = officer.assignment
            crime = assignment[0] if assignment else None
            if officer.arrest():
                arrests += 1
                if crime is not None:
                    solved_crime_ids.add(id(crime))
                self.history.append(f"Criminal arrested by {officer.lastname}")
                details.append(f"{officer.lastname} made an arrest")
            else:
                failed += 1
                details.append(f"{officer.lastname} failed to arrest suspect")

        removed_count = 0
        for crime in list(self.applications):
            if id(crime) in solved_crime_ids:
                self.applications.remove(crime)
                removed_count += 1

        self._update_security()
        details.append(f"Successful: {arrests}")
        details.append(f"Failed: {failed}")
        details.append(f"Crimes removed: {removed_count}")
        details.append(f"Overall security: {self.security.level:.2f}/10.00")
        return OperationResult(True, "Arrest processing completed", details=details)

    def list_history(self) -> list[str]:
        return list(self.history)

    def clear_history(self) -> OperationResult:
        self.history.clear()
        return OperationResult(True, "History cleared")

    def add_law(self, article: int, severity: int, desc: str) -> OperationResult:
        law = Law(article=article, severity=severity, desc=desc)
        self.laws.append(law)
        self.history.append(f"Law added: Article {article}")
        return OperationResult(True, f"Law added: Article {article} (Severity: {severity})", data=law)

    def list_laws(self) -> list[Law]:
        return list(self.laws)


PoliceSystemFacade = PoliceSystem
