from services.lab_service import LabService
from ui.formatter import OutputFormatter


class CommandLineInterface:
    """CLI controller; later can be replaced by GUI without touching domain layer."""

    def __init__(self) -> None:
        self.service = LabService()
        self.formatter = OutputFormatter()

    def run(self) -> None:
        print("OOP scaffold is ready. Implement menu/actions in this class.")
