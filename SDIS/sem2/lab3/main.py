from pathlib import Path

from reversi.ui import run_app


def main() -> None:
    run_app(Path(__file__).resolve().parent)


if __name__ == "__main__":  # pragma: no cover
    main()
