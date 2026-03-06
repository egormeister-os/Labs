from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent / "src"))

from ui.cli import CommandLineInterface


def main() -> None:
    cli = CommandLineInterface()
    cli.run()


if __name__ == "__main__":
    main()
