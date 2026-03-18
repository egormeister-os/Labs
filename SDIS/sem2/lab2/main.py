from __future__ import annotations

import sys
from pathlib import Path

from PyQt5.QtWidgets import QApplication

from app.controllers import AppController
from app.views import MainWindow


def main() -> int:
    base_dir = Path(__file__).resolve().parent
    data_dir = base_dir / "data"
    data_dir.mkdir(exist_ok=True)
    database_path = data_dir / "tournaments.db"

    app = QApplication(sys.argv)
    app.setApplicationName("Каталог турниров")

    controller = AppController(database_path)
    window = MainWindow(controller)
    window.show()

    return app.exec_()


if __name__ == "__main__":
    raise SystemExit(main())
