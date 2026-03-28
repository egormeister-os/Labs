import argparse


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="CLI entry point for lab4. Later connect it to the shared PoliceSystemFacade."
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show that the CLI entry point is wired and ready.",
    )
    return parser


def main() -> None:
    parser = create_parser()
    args = parser.parse_args()
    if args.status:
        print("CLI scaffold for lab4 is ready.")
        return
    parser.print_help()


if __name__ == "__main__":
    main()
