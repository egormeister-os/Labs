#!/usr/bin/env python3
"""
Police Management System - Command Line Interface

A system for managing police stations, crimes, investigations,
and maintaining public order.
"""

import argparse
import pickle
import shlex
import sys
from pathlib import Path
from typing import Any

from police import (
    Police,
    Policeman,
    Citizen,
    Crime,
    Investigation,
    Law,
    Security,
    ZoneNotFoundError,
    PolicemanNotFoundError,
)


DATA_DIR = Path("data")
DATA_FILES = {
    "police": "police.pkl",
    "applications": "applications.pkl",
    "history": "history.pkl",
    "citizens": "citizens.pkl",
    "laws": "laws.pkl",
    "security": "security.pkl",
}


class PoliceSystem:
    """Main system class managing all police operations."""

    def __init__(self) -> None:
        self.data_dir = DATA_DIR
        self.data_dir.mkdir(exist_ok=True)
        self._load_data()

    def _load_data(self) -> None:
        """Load data from pickle files or initialize defaults."""
        defaults: dict[str, Any] = {
            "police": Police(),
            "applications": [],
            "history": [],
            "laws": [
                Law(101, severity=1, desc="Minor offense"),
                Law(201, severity=3, desc="Theft"),
                Law(301, severity=5, desc="Violent crime"),
            ],
            "security": Security(),
            "citizens": [],
        }

        for key, filename in DATA_FILES.items():
            path = self.data_dir / filename
            try:
                with open(path, "rb") as f:
                    setattr(self, key, pickle.load(f))
                print(f"✓ Loaded: {filename}")
            except (FileNotFoundError, EOFError, pickle.UnpicklingError):
                setattr(self, key, defaults[key])
                print(f"⚠ Initialized: {filename}")

    def save_data(self) -> None:
        """Save all data to pickle files."""
        data_to_save = {
            "police": self.police,
            "applications": self.applications,
            "history": self.history,
            "citizens": self.citizens,
            "laws": self.laws,
            "security": self.security,
        }

        for key, obj in data_to_save.items():
            path = self.data_dir / DATA_FILES[key]
            with open(path, "wb") as f:
                pickle.dump(obj, f)
        print("✓ Data saved successfully")

    def _update_security(self) -> None:
        """Update security levels for all zones."""
        # Count citizens by zone
        citizens_by_zone: dict[str, int] = {}
        for zone in self.police.zones:
            citizens_by_zone[zone] = 0
        for citizen in self.citizens:
            if citizen.zone and citizen.zone in citizens_by_zone:
                citizens_by_zone[citizen.zone] += 1

        # Count crimes per zone
        crimes_by_zone: dict[str, int] = {}
        for zone in self.police.zones:
            crimes_by_zone[zone] = 0
        for crime in self.applications:
            if crime.zone in crimes_by_zone:
                crimes_by_zone[crime.zone] += 1

        # Update security for each zone based on its own citizens and crimes
        self.police.update_all_zones_security(citizens_by_zone, crimes_by_zone)

        # Also update global security
        self.security.eval(self.citizens, self.applications)

    # Statement operations
    def create_statement(self, description: str, zone: str, suspect_idx: int, law_idx: int) -> None:
        """Create a new crime statement."""
        if not self.citizens:
            print("✗ No citizens registered")
            return
        if not self.laws:
            print("✗ No laws defined")
            return
        if not self.police.has_zone(zone):
            print(f"✗ Zone '{zone}' does not exist")
            return

        if suspect_idx < 0 or law_idx < 0:
            print("✗ Invalid citizen or law index")
            return

        try:
            suspect = self.citizens[suspect_idx]
            law = self.laws[law_idx]
        except IndexError:
            print("✗ Invalid citizen or law index")
            return

        application = Crime(
            suspect=suspect,
            description=description,
            zone=zone,
            law=law
        )
        self.applications.append(application)
        self._update_security()
        self.history.append(f"Crime report filed: {application.suspect.name} - {description}")
        print(f"✓ Crime report filed successfully")

    def delete_statement(self, index: int) -> None:
        """Delete a crime statement by index."""
        if index < 0:
            print("✗ Invalid application index")
            return
        try:
            removed = self.applications.pop(index)
            self._update_security()
            self.history.append(f"Application deleted: {removed.description}")
            print(f"✓ Application deleted")
        except IndexError:
            print("✗ Invalid application index")

    def show_statements(self) -> None:
        """Display all crime statements."""
        if not self.applications:
            print("No crime reports filed")
            return
        for i, app in enumerate(self.applications):
            print(f"[{i}] {app}")

    # Citizen operations
    def add_citizen(self, name: str, zone: str | None = None) -> None:
        """Add a new citizen."""
        citizen = Citizen(name=name, zone=zone)
        self.citizens.append(citizen)
        self._update_security()
        self.history.append(f"Citizen added: {name}")
        print(f"✓ Citizen '{name}' added")

    def delete_citizen(self, index: int) -> None:
        """Delete a citizen by index."""
        if index < 0:
            print("✗ Invalid citizen index")
            return
        try:
            removed = self.citizens.pop(index)
            self._update_security()
            self.history.append(f"Citizen removed: {removed.name}")
            print(f"✓ Citizen removed")
        except IndexError:
            print("✗ Invalid citizen index")

    def show_citizens(self) -> None:
        """Display all citizens."""
        if not self.citizens:
            print("No citizens registered")
            return
        for i, citizen in enumerate(self.citizens):
            print(f"[{i}] {citizen}")

    # Police operations
    def hire_policeman(self, lastname: str, zone: str) -> None:
        """Hire a new policeman to a zone."""
        if not self.police.has_zone(zone):
            print(f"✗ Zone '{zone}' does not exist. Create it first.")
            return
        policeman = Policeman(lastname=lastname, zone=zone)
        self.police.hire(policeman=policeman, zone=zone)
        self.history.append(f"Policeman {lastname} hired to zone {zone}")
        print(f"✓ Officer {lastname} hired to zone {zone}")

    def fire_policeman(self, lastname: str) -> None:
        """Fire a policeman by lastname."""
        policemen = self.police.get_policemen()
        for policeman in policemen:
            if policeman.lastname == lastname:
                try:
                    self.police.fire(policeman)
                    self.history.append(f"Policeman {lastname} fired")
                    print(f"✓ Officer {lastname} fired")
                    return
                except (ZoneNotFoundError, PolicemanNotFoundError) as e:
                    print(f"✗ Error: {e}")
                    return
        print(f"✗ Policeman '{lastname}' not found")

    def add_zone(self, zone: str) -> None:
        """Add a new zone."""
        try:
            self.police.add_zone(zone)
            self.history.append(f"Zone '{zone}' created")
            print(f"✓ Zone '{zone}' created")
        except Exception as e:
            print(f"✗ Error: {e}")

    def show_policemen(self) -> None:
        """Display all policemen with indexes and fatigue."""
        policemen = self.police.get_policemen()
        if not policemen:
            print("No policemen hired")
            return
        for i, policeman in enumerate(policemen):
            print(f"[{i}] {policeman}")

    def recover_policemen(self) -> None:
        """Recover all resting officers."""
        recovered = 0
        for officer in self.police.get_policemen():
            if officer.is_resting:
                officer.recovery()
                recovered += 1
        if recovered > 0:
            print(f"✓ {recovered} officer(s) recovered from rest")
        else:
            print("No officers need recovery")

    def show_info(self) -> None:
        """Display detailed zone information with fatigue levels."""
        if not self.police.zones:
            print("No zones registered")
            return

        for zone_id, data in sorted(self.police.zones.items()):
            print(f"\n{'='*50}")
            print(f"Zone: {zone_id}")
            print(f"{'='*50}")
            print(f"  Officers: {len(data['policemen'])}")
            for policeman in data["policemen"]:
                if policeman.is_resting:
                    fatigue_status = "⏸️ Resting"
                elif policeman.fatigue < 3:
                    fatigue_status = "🟢 Fresh"
                elif policeman.fatigue < 6:
                    fatigue_status = "🟡 Tired"
                else:
                    fatigue_status = "🔴 Exhausted"
                assignment = " [ASSIGNED]" if policeman.has_assignment else ""
                rest_mark = " [RESTING]" if policeman.is_resting else ""
                print(f"    - {policeman.lastname} | Fatigue: {fatigue_status}{assignment}{rest_mark}")
            
            # Show crimes from applications (source of truth) for this zone
            zone_crimes = [c for c in self.applications if c.zone == zone_id]
            print(f"\n  Crimes: {len(zone_crimes)}")
            for crime in zone_crimes:
                print(f"    - {crime.description} (Severity: {crime.severity})")
            print(f"\n  Security Level: {data['security']:.2f}/10.00")

    def relocate_policemen(self, indexes: list[int], target_zone: str) -> None:
        """Relocate policemen to a new zone."""
        if not self.police.has_zone(target_zone):
            print(f"✗ Target zone '{target_zone}' does not exist")
            return
        if any(i < 0 for i in indexes):
            print("✗ Invalid policeman index")
            return

        policemen = self.police.get_policemen()
        try:
            relocated = [policemen[i] for i in indexes]
            self.police.relocate(relocated_policemen=relocated, target_zone=target_zone)
            self.history.append(f"Policemen relocated to zone {target_zone}")
            print(f"✓ Officers relocated to zone {target_zone}")
            # Show new distribution
            print(f"\nNew distribution in {target_zone}:")
            for officer in self.police.get_policemen_by_zone(target_zone):
                print(f"  - {officer.lastname}")
        except IndexError:
            print("✗ Invalid policeman index")
        except (ZoneNotFoundError, PolicemanNotFoundError) as e:
            print(f"✗ Error: {e}")

    # Investigation operations
    def investigate_crimes(self, do_arrest: bool = False) -> None:
        """
        Investigate ALL pending crimes and optionally attempt arrests.

        Args:
            do_arrest: If True, attempt arrests immediately after investigation.
        """
        if not self.applications:
            print("No crimes to investigate")
            return

        # Clear any stale assignments from previous investigations
        for officer in self.police.get_policemen():
            officer.clear_assignment()

        investigation = Investigation(self.applications)
        results = investigation.investigate_all()

        if not results:
            print("✗ Investigation inconclusive for all crimes")
            return

        print(f"✓ Investigation completed for {len(results)} crime(s):\n")

        # Only consider officers who are not resting and have no assignment
        available_officers = [
            p for p in self.police.get_policemen() 
            if not p.has_assignment and not p.is_resting
        ]
        officer_idx = 0
        assigned_count = 0

        for crime, severity in results:
            print(f"  • {crime.suspect.name} is likely guilty")
            print(f"    Crime: {crime.description}, Severity: {severity}")

            # Assign to available officer
            if officer_idx < len(available_officers):
                officer = available_officers[officer_idx]
                officer.assign_crime((crime, severity))
                print(f"    Assigned to: {officer.lastname} ({officer.zone})\n")
                officer_idx += 1
                assigned_count += 1
            else:
                print(f"    ⚠ No available officer for assignment\n")

        if assigned_count == 0:
            print("⚠ No officers available for arrest assignments")

        # If do_arrest is True, attempt arrests immediately
        if do_arrest:
            self._perform_arrests_and_cleanup()

    def _perform_arrests_and_cleanup(self) -> None:
        """
        Attempt arrests for all assigned officers and remove solved crimes.
        
        This method:
        1. Attempts arrest for each officer with an assignment
        2. Removes crime from applications and zone on successful arrest
        3. Updates security levels
        4. Shows summary of results
        """
        officers = self.police.get_policemen()
        arrests = 0
        failed = 0
        solved_crime_ids: set[int] = set()

        print("\n🚔 Attempting arrests...\n")
        
        for officer in officers:
            if officer.has_assignment:
                assignment = officer.assignment
                crime = assignment[0] if assignment else None
                
                if officer.arrest():
                    arrests += 1
                    if crime is not None:
                        solved_crime_ids.add(id(crime))
                    self.history.append(f"Criminal arrested by {officer.lastname}")
                    print(f"  ✓ {officer.lastname} made an arrest!")
                else:
                    failed += 1
                    print(f"  ✗ {officer.lastname} failed to arrest suspect")

        # Remove solved crimes from applications
        removed_count = 0
        for crime in list(self.applications):
            if id(crime) in solved_crime_ids:
                self.applications.remove(crime)
                removed_count += 1

        # Summary
        print(f"\nArrest Summary:")
        print(f"  Successful: {arrests}")
        print(f"  Failed: {failed}")
        print(f"  Crimes removed: {removed_count}")

        # Update and show security after arrests
        self._update_security()
        print(f"\nUpdated Security Levels:")
        for zone_id, data in sorted(self.police.zones.items()):
            print(f"  {zone_id}: {data['security']:.2f}/10.00")
        print(f"  Overall: {self.security.level:.2f}/10.00")

    def arrest_criminals(self) -> None:
        """Attempt to arrest assigned criminals (standalone command)."""
        self._perform_arrests_and_cleanup()

    # History operations
    def show_history(self) -> None:
        """Display system history."""
        if not self.history:
            print("History is empty")
            return
        for entry in self.history:
            print(f"  • {entry}")

    def clear_history(self) -> None:
        """Clear system history."""
        self.history.clear()
        print("✓ History cleared")

    # Law operations
    def add_law(self, article: int, severity: int, desc: str) -> None:
        """Add a new law."""
        law = Law(article=article, severity=severity, desc=desc)
        self.laws.append(law)
        self.history.append(f"Law added: Article {article}")
        print(f"✓ Law added: Article {article} (Severity: {severity})")

    def show_laws(self) -> None:
        """Display all laws."""
        if not self.laws:
            print("No laws defined")
            return
        for i, law in enumerate(self.laws):
            print(f"[{i}] {law} - {law.desc}")


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        description="""Police Management System - A CLI application for managing police departments,
crime investigations, and maintaining public order.

Examples:
  %(prog)s citizen add "John Doe"     Add a new citizen
  %(prog)s police add-zone Downtown   Create a new zone
  %(prog)s police hire Smith Downtown Hire an officer
  %(prog)s investigate --arrest       Investigate and arrest
  %(prog)s police info                Show zone details with fatigue
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands", required=True)

    # Statement commands
    stmt_parser = subparsers.add_parser("statement", help="Crime statement operations")
    stmt_sub = stmt_parser.add_subparsers(dest="subcommand", required=True)

    stmt_add = stmt_sub.add_parser("add", help="File a crime report")
    stmt_add.add_argument("description", help="Crime description")
    stmt_add.add_argument("zone", help="Zone where crime occurred")
    stmt_add.add_argument("suspect_idx", type=int, help="Suspect citizen index")
    stmt_add.add_argument("law_idx", type=int, help="Law index")

    stmt_del = stmt_sub.add_parser("delete", help="Delete a crime report")
    stmt_del.add_argument("index", type=int, help="Report index")

    stmt_sub.add_parser("list", help="List all crime reports")

    # Citizen commands
    cit_parser = subparsers.add_parser("citizen", help="Citizen operations")
    cit_sub = cit_parser.add_subparsers(dest="subcommand", required=True)

    cit_add = cit_sub.add_parser("add", help="Add a citizen")
    cit_add.add_argument("name", help="Citizen name")
    cit_add.add_argument("--zone", "-z", help="Citizen's zone")

    cit_del = cit_sub.add_parser("delete", help="Delete a citizen")
    cit_del.add_argument("index", type=int, help="Citizen index")

    cit_sub.add_parser("list", help="List all citizens")

    # Police commands
    pol_parser = subparsers.add_parser("police", help="Police operations")
    pol_sub = pol_parser.add_subparsers(dest="subcommand", required=True)

    pol_hire = pol_sub.add_parser("hire", help="Hire a policeman")
    pol_hire.add_argument("lastname", help="Officer lastname")
    pol_hire.add_argument("zone", help="Zone assignment")

    pol_fire = pol_sub.add_parser("fire", help="Fire a policeman")
    pol_fire.add_argument("lastname", help="Officer lastname")

    pol_zone = pol_sub.add_parser("add-zone", help="Add a new zone")
    pol_zone.add_argument("zone", help="Zone name")

    pol_sub.add_parser("list", help="List all officers")
    pol_sub.add_parser("info", help="Show zone information with fatigue levels")
    pol_sub.add_parser("recover", help="Recover all resting officers")

    pol_reloc = pol_sub.add_parser("relocate", help="Relocate officers")
    pol_reloc.add_argument("indexes", type=int, nargs="+", help="Officer indexes")
    pol_reloc.add_argument("target_zone", help="Target zone")

    # Investigation commands
    inv_parser = subparsers.add_parser("investigate", help="Investigate crimes")
    inv_parser.add_argument("--arrest", "-a", action="store_true", help="Attempt arrests after investigation")

    # History commands
    hist_parser = subparsers.add_parser("history", help="History operations")
    hist_sub = hist_parser.add_subparsers(dest="subcommand", required=True)
    hist_sub.add_parser("show", help="Show history")
    hist_sub.add_parser("clear", help="Clear history")

    # Law commands
    law_parser = subparsers.add_parser("law", help="Law operations")
    law_sub = law_parser.add_subparsers(dest="subcommand", required=True)

    law_add = law_sub.add_parser("add", help="Add a law")
    law_add.add_argument("article", type=int, help="Article number")
    law_add.add_argument("severity", type=int, help="Severity (1-5)")
    law_add.add_argument("desc", help="Description")

    law_sub.add_parser("list", help="List all laws")

    # System commands
    subparsers.add_parser("save", help="Save data and exit")
    subparsers.add_parser("exit", help="Exit the system")

    return parser


def print_help() -> None:
    """Print interactive mode help."""
    print("""
╔═══════════════════════════════════════════════════════════╗
║           POLICE MANAGEMENT SYSTEM - HELP                 ║
╠═══════════════════════════════════════════════════════════╣
║  CITIZEN COMMANDS:                                        ║
║    citizen add <name>         - Add a citizen             ║
║    citizen delete <index>     - Remove a citizen          ║
║    citizen list               - Show all citizens         ║
║                                                           ║
║  POLICE COMMANDS:                                         ║
║    police hire <lastname> <zone>  - Hire an officer       ║
║    police fire <lastname>         - Fire an officer       ║
║    police add-zone <zone>         - Create a zone         ║
║    police list                    - Show all officers     ║
║    police info                    - Show zone details     ║
║    police recover                 - Recover resting officers ║
║    police relocate <idx...> <zone>- Move officers         ║
║                                                           ║
║  CRIME COMMANDS:                                          ║
║    statement add <desc> <zone> <suspect_idx> <law_idx>    ║
║    statement delete <index>       - Remove a report       ║
║    statement list                 - Show all reports      ║
║                                                           ║
║  INVESTIGATION:                                           ║
║    investigate                    - Analyze crimes        ║
║    investigate --arrest           - Investigate + arrest  ║
║                                                           ║
║  LAW COMMANDS:                                            ║
║    law add <article> <severity> <desc> - Add a law        ║
║    law list                          - Show all laws      ║
║                                                           ║
║  SYSTEM:                                                  ║
║    history show                   - View history          ║
║    history clear                  - Clear history         ║
║    save                           - Save and continue     ║
║    exit, quit, q                  - Save and exit         ║
║    help, ?                        - Show this help        ║
╚═══════════════════════════════════════════════════════════╝
""")


def interactive_mode(system: PoliceSystem) -> None:
    """Run the system in interactive mode."""
    print("\n" + "="*50)
    print("  POLICE MANAGEMENT SYSTEM")
    print("="*50)
    print("\nType 'help' or '?' for available commands")
    print("Use --help with commands for details (e.g., 'police --help')\n")

    while True:
        try:
            user_input = input("police> ").strip()
            if not user_input:
                continue

            args = shlex.split(user_input)
            command = args[0]

            if command in ("exit", "quit", "q"):
                system.save_data()
                print("Goodbye!")
                break

            elif command in ("help", "?"):
                print_help()

            elif command == "save":
                system.save_data()

            elif command == "statement":
                if len(args) < 2:
                    print("Usage: statement <add|delete|list> [args...]")
                    print("       statement add <desc> <zone> <suspect_idx> <law_idx>")
                    continue
                subcmd = args[1]
                if subcmd == "add":
                    if len(args) < 6:
                        print("Usage: statement add <desc> <zone> <suspect_idx> <law_idx>")
                        continue
                    system.create_statement(args[2], args[3], int(args[4]), int(args[5]))
                elif subcmd == "delete":
                    if len(args) < 3:
                        print("Usage: statement delete <index>")
                        continue
                    system.delete_statement(int(args[2]))
                elif subcmd == "list":
                    system.show_statements()

            elif command == "citizen":
                if len(args) < 2:
                    print("Usage: citizen <add|delete|list> [args...]")
                    continue
                subcmd = args[1]
                if subcmd == "add":
                    if len(args) < 3:
                        print("Usage: citizen add <name> [--zone <zone>]")
                        continue
                    # Parse optional --zone argument
                    zone = None
                    if "--zone" in args or "-z" in args:
                        try:
                            z_idx = args.index("--zone") if "--zone" in args else args.index("-z")
                            if z_idx + 1 < len(args):
                                zone = args[z_idx + 1]
                        except (ValueError, IndexError):
                            pass
                    system.add_citizen(args[2], zone=zone)
                elif subcmd == "delete":
                    if len(args) < 3:
                        print("Usage: citizen delete <index>")
                        continue
                    system.delete_citizen(int(args[2]))
                elif subcmd == "list":
                    system.show_citizens()

            elif command == "police":
                if len(args) < 2:
                    print("Usage: police <hire|fire|add-zone|list|info|relocate> [args...]")
                    continue
                subcmd = args[1]
                if subcmd == "hire":
                    if len(args) < 4:
                        print("Usage: police hire <lastname> <zone>")
                        continue
                    system.hire_policeman(args[2], args[3])
                elif subcmd == "fire":
                    if len(args) < 3:
                        print("Usage: police fire <lastname>")
                        continue
                    system.fire_policeman(args[2])
                elif subcmd == "add-zone":
                    if len(args) < 3:
                        print("Usage: police add-zone <zone>")
                        continue
                    system.add_zone(args[2])
                elif subcmd == "list":
                    system.show_policemen()
                elif subcmd == "info":
                    system.show_info()
                elif subcmd == "recover":
                    system.recover_policemen()
                elif subcmd == "relocate":
                    if len(args) < 4:
                        print("Usage: police relocate <idx1> [idx2...] <target_zone>")
                        continue
                    # Last arg is zone, rest are indexes
                    target_zone = args[-1]
                    indexes = [int(x) for x in args[2:-1]]
                    system.relocate_policemen(indexes, target_zone)

            elif command == "investigate":
                do_arrest = "--arrest" in args or "-a" in args
                system.investigate_crimes(do_arrest=do_arrest)

            elif command == "history":
                if len(args) < 2:
                    print("Usage: history <show|clear>")
                    continue
                subcmd = args[1]
                if subcmd == "show":
                    system.show_history()
                elif subcmd == "clear":
                    system.clear_history()

            elif command == "law":
                if len(args) < 2:
                    print("Usage: law <add|list> [args...]")
                    continue
                subcmd = args[1]
                if subcmd == "add":
                    if len(args) < 5:
                        print("Usage: law add <article> <severity> <desc>")
                        continue
                    system.add_law(int(args[2]), int(args[3]), args[4])
                elif subcmd == "list":
                    system.show_laws()

            else:
                print(f"Unknown command: {command}")
                print("Type 'help' for available commands")

        except KeyboardInterrupt:
            print("\nUse 'exit' or 'save' to save and quit")
        except Exception as e:
            print(f"✗ Error: {e}")


def main() -> None:
    """Main entry point."""
    parser = create_parser()
    
    # Check if help is requested
    if len(sys.argv) == 1:
        # No arguments - run interactive mode
        system = PoliceSystem()
        interactive_mode(system)
        return
    
    args = parser.parse_args()

    system = PoliceSystem()

    # Command-line mode
    try:
        if args.command == "save":
            system.save_data()
        elif args.command == "exit":
            system.save_data()
            print("Goodbye!")
        elif args.command == "statement":
            if args.subcommand == "add":
                system.create_statement(
                    args.description, args.zone, args.suspect_idx, args.law_idx
                )
            elif args.subcommand == "delete":
                system.delete_statement(args.index)
            elif args.subcommand == "list":
                system.show_statements()
        elif args.command == "citizen":
            if args.subcommand == "add":
                system.add_citizen(args.name, zone=args.zone)
            elif args.subcommand == "delete":
                system.delete_citizen(args.index)
            elif args.subcommand == "list":
                system.show_citizens()
        elif args.command == "police":
            if args.subcommand == "hire":
                system.hire_policeman(args.lastname, args.zone)
            elif args.subcommand == "fire":
                system.fire_policeman(args.lastname)
            elif args.subcommand == "add-zone":
                system.add_zone(args.zone)
            elif args.subcommand == "list":
                system.show_policemen()
            elif args.subcommand == "info":
                system.show_info()
            elif args.subcommand == "recover":
                system.recover_policemen()
            elif args.subcommand == "relocate":
                system.relocate_policemen(args.indexes, args.target_zone)
        elif args.command == "investigate":
            system.investigate_crimes(do_arrest=args.arrest)
        elif args.command == "history":
            if args.subcommand == "show":
                system.show_history()
            elif args.subcommand == "clear":
                system.clear_history()
        elif args.command == "law":
            if args.subcommand == "add":
                system.add_law(args.article, args.severity, args.desc)
            elif args.subcommand == "list":
                system.show_laws()

        # Auto-save after commands
        system.save_data()

    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
