from __future__ import annotations

import argparse
import shlex
import sys

from app.services import OperationResult, PoliceSystem


def _print_result(result: OperationResult) -> None:
    prefix = "✓" if result.ok else "✗"
    print(f"{prefix} {result.message}")
    for detail in result.details:
        print(f"  {detail}")


def _print_indexed(items: list[object], empty_message: str) -> None:
    if not items:
        print(empty_message)
        return
    for index, item in enumerate(items):
        print(f"[{index}] {item}")


def _print_zone_info(system: PoliceSystem) -> None:
    zone_info = system.get_zone_info()
    if not zone_info:
        print("No zones registered")
        return

    for zone in zone_info:
        print(f"\n{'=' * 50}")
        print(f"Zone: {zone['zone']}")
        print(f"{'=' * 50}")
        print(f"  Officers: {len(zone['officers'])}")
        for officer in zone["officers"]:
            assignment = " [ASSIGNED]" if officer["has_assignment"] else ""
            rest_mark = " [RESTING]" if officer["is_resting"] else ""
            print(
                f"    - {officer['lastname']} | Fatigue: {officer['fatigue_status']}"
                f"{assignment}{rest_mark}"
            )

        print(f"\n  Crimes: {len(zone['crimes'])}")
        for crime in zone["crimes"]:
            print(f"    - {crime.description} (Severity: {crime.severity})")
        print(f"\n  Security Level: {zone['security']:.2f}/10.00")


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="""Police Management System - CLI for managing police departments,
crime investigations, and public order.""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands", required=True)

    stmt_parser = subparsers.add_parser("statement", help="Crime statement operations")
    stmt_sub = stmt_parser.add_subparsers(dest="subcommand", required=True)
    stmt_add = stmt_sub.add_parser("add", help="File a crime report")
    stmt_add.add_argument("description")
    stmt_add.add_argument("zone")
    stmt_add.add_argument("suspect_idx", type=int)
    stmt_add.add_argument("law_idx", type=int)
    stmt_del = stmt_sub.add_parser("delete", help="Delete a crime report")
    stmt_del.add_argument("index", type=int)
    stmt_sub.add_parser("list", help="List all crime reports")

    cit_parser = subparsers.add_parser("citizen", help="Citizen operations")
    cit_sub = cit_parser.add_subparsers(dest="subcommand", required=True)
    cit_add = cit_sub.add_parser("add", help="Add a citizen")
    cit_add.add_argument("name")
    cit_add.add_argument("--zone", "-z")
    cit_del = cit_sub.add_parser("delete", help="Delete a citizen")
    cit_del.add_argument("index", type=int)
    cit_sub.add_parser("list", help="List all citizens")

    pol_parser = subparsers.add_parser("police", help="Police operations")
    pol_sub = pol_parser.add_subparsers(dest="subcommand", required=True)
    pol_hire = pol_sub.add_parser("hire", help="Hire a policeman")
    pol_hire.add_argument("lastname")
    pol_hire.add_argument("zone")
    pol_fire = pol_sub.add_parser("fire", help="Fire a policeman")
    pol_fire.add_argument("lastname")
    pol_zone = pol_sub.add_parser("add-zone", help="Add a new zone")
    pol_zone.add_argument("zone")
    pol_sub.add_parser("list", help="List all officers")
    pol_sub.add_parser("info", help="Show zone information with fatigue levels")
    pol_sub.add_parser("recover", help="Recover all resting officers")
    pol_reloc = pol_sub.add_parser("relocate", help="Relocate officers")
    pol_reloc.add_argument("indexes", type=int, nargs="+")
    pol_reloc.add_argument("target_zone")

    inv_parser = subparsers.add_parser("investigate", help="Investigate crimes")
    inv_parser.add_argument("--arrest", "-a", action="store_true")

    hist_parser = subparsers.add_parser("history", help="History operations")
    hist_sub = hist_parser.add_subparsers(dest="subcommand", required=True)
    hist_sub.add_parser("show", help="Show history")
    hist_sub.add_parser("clear", help="Clear history")

    law_parser = subparsers.add_parser("law", help="Law operations")
    law_sub = law_parser.add_subparsers(dest="subcommand", required=True)
    law_add = law_sub.add_parser("add", help="Add a law")
    law_add.add_argument("article", type=int)
    law_add.add_argument("severity", type=int)
    law_add.add_argument("desc")
    law_sub.add_parser("list", help="List all laws")

    subparsers.add_parser("save", help="Save data and exit")
    subparsers.add_parser("exit", help="Exit the system")
    return parser


def print_help() -> None:
    print(
        """
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
"""
    )


def dispatch(system: PoliceSystem, args: argparse.Namespace) -> None:
    if args.command == "save":
        _print_result(system.save_data())
        return

    if args.command == "exit":
        _print_result(system.save_data())
        print("Goodbye!")
        return

    if args.command == "statement":
        if args.subcommand == "add":
            _print_result(
                system.create_statement(args.description, args.zone, args.suspect_idx, args.law_idx)
            )
        elif args.subcommand == "delete":
            _print_result(system.delete_statement(args.index))
        elif args.subcommand == "list":
            _print_indexed(system.list_statements(), "No crime reports filed")
        return

    if args.command == "citizen":
        if args.subcommand == "add":
            _print_result(system.add_citizen(args.name, zone=args.zone))
        elif args.subcommand == "delete":
            _print_result(system.delete_citizen(args.index))
        elif args.subcommand == "list":
            _print_indexed(system.list_citizens(), "No citizens registered")
        return

    if args.command == "police":
        if args.subcommand == "hire":
            _print_result(system.hire_policeman(args.lastname, args.zone))
        elif args.subcommand == "fire":
            _print_result(system.fire_policeman(args.lastname))
        elif args.subcommand == "add-zone":
            _print_result(system.add_zone(args.zone))
        elif args.subcommand == "list":
            _print_indexed(system.list_policemen(), "No policemen hired")
        elif args.subcommand == "info":
            _print_zone_info(system)
        elif args.subcommand == "recover":
            _print_result(system.recover_policemen())
        elif args.subcommand == "relocate":
            _print_result(system.relocate_policemen(args.indexes, args.target_zone))
        return

    if args.command == "investigate":
        _print_result(system.investigate_crimes(do_arrest=args.arrest))
        return

    if args.command == "history":
        if args.subcommand == "show":
            history = system.list_history()
            if not history:
                print("History is empty")
            else:
                for entry in history:
                    print(f"  • {entry}")
        elif args.subcommand == "clear":
            _print_result(system.clear_history())
        return

    if args.command == "law":
        if args.subcommand == "add":
            _print_result(system.add_law(args.article, args.severity, args.desc))
        elif args.subcommand == "list":
            laws = system.list_laws()
            if not laws:
                print("No laws defined")
            else:
                for index, law in enumerate(laws):
                    print(f"[{index}] {law} - {law.desc}")


def interactive_mode(system: PoliceSystem) -> None:
    print("\n" + "=" * 50)
    print("  POLICE MANAGEMENT SYSTEM")
    print("=" * 50)
    print("\nType 'help' or '?' for available commands")
    print("Use --help with commands for details (e.g., 'police --help')\n")

    parser = create_parser()
    while True:
        try:
            user_input = input("police> ").strip()
            if not user_input:
                continue

            args = shlex.split(user_input)
            command = args[0]
            if command in ("exit", "quit", "q"):
                _print_result(system.save_data())
                print("Goodbye!")
                break
            if command in ("help", "?"):
                print_help()
                continue

            parsed_args = parser.parse_args(args)
            dispatch(system, parsed_args)
        except KeyboardInterrupt:
            print("\nUse 'exit' or 'save' to save and quit")
        except SystemExit:
            continue
        except Exception as exc:
            print(f"✗ Error: {exc}")


def main() -> None:
    parser = create_parser()
    if len(sys.argv) == 1:
        interactive_mode(PoliceSystem())
        return

    args = parser.parse_args()
    system = PoliceSystem()
    try:
        dispatch(system, args)
        if args.command not in {"save", "exit"}:
            _print_result(system.save_data())
    except Exception as exc:
        print(f"✗ Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
