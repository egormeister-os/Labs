"""Extended tests to improve coverage for main.py."""

from __future__ import annotations

import pickle
from pathlib import Path

import pytest

import main
from police import Citizen, Crime, Investigation, Law, Police, Policeman, Security


class StubSystem:
    """Lightweight stub used to verify CLI dispatch behavior."""

    def __init__(self, raise_on: set[str] | None = None) -> None:
        self.calls: list[tuple[str, tuple, dict]] = []
        self._raise_on = raise_on or set()

    def _record(self, name: str, *args, **kwargs) -> None:
        self.calls.append((name, args, kwargs))
        if name in self._raise_on:
            raise RuntimeError("boom")

    def save_data(self) -> None:
        self._record("save_data")

    def create_statement(self, *args, **kwargs) -> None:
        self._record("create_statement", *args, **kwargs)

    def delete_statement(self, *args, **kwargs) -> None:
        self._record("delete_statement", *args, **kwargs)

    def show_statements(self) -> None:
        self._record("show_statements")

    def add_citizen(self, *args, **kwargs) -> None:
        self._record("add_citizen", *args, **kwargs)

    def delete_citizen(self, *args, **kwargs) -> None:
        self._record("delete_citizen", *args, **kwargs)

    def show_citizens(self) -> None:
        self._record("show_citizens")

    def hire_policeman(self, *args, **kwargs) -> None:
        self._record("hire_policeman", *args, **kwargs)

    def fire_policeman(self, *args, **kwargs) -> None:
        self._record("fire_policeman", *args, **kwargs)

    def add_zone(self, *args, **kwargs) -> None:
        self._record("add_zone", *args, **kwargs)

    def show_policemen(self) -> None:
        self._record("show_policemen")

    def show_info(self) -> None:
        self._record("show_info")

    def recover_policemen(self) -> None:
        self._record("recover_policemen")

    def relocate_policemen(self, *args, **kwargs) -> None:
        self._record("relocate_policemen", *args, **kwargs)

    def investigate_crimes(self, *args, **kwargs) -> None:
        self._record("investigate_crimes", *args, **kwargs)

    def show_history(self) -> None:
        self._record("show_history")

    def clear_history(self) -> None:
        self._record("clear_history")

    def add_law(self, *args, **kwargs) -> None:
        self._record("add_law", *args, **kwargs)

    def show_laws(self) -> None:
        self._record("show_laws")


def _run_interactive(monkeypatch: pytest.MonkeyPatch, system: StubSystem, commands: list[object]) -> None:
    """Run interactive_mode with deterministic fake input."""
    sequence = iter(commands)

    def fake_input(_prompt: str) -> str:
        item = next(sequence)
        if isinstance(item, BaseException):
            raise item
        return str(item)

    monkeypatch.setattr("builtins.input", fake_input)
    main.interactive_mode(system)  # type: ignore[arg-type]


@pytest.fixture
def real_system(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> main.PoliceSystem:
    """Create real PoliceSystem isolated from repository data folder."""
    monkeypatch.setattr(main, "DATA_DIR", tmp_path / "data")
    system = main.PoliceSystem()
    system.police = Police()
    system.applications = []
    system.history = []
    system.citizens = []
    system.laws = [Law(101, severity=1, desc="Minor offense")]
    system.security = Security()
    return system


def _install_stub_factory(
    monkeypatch: pytest.MonkeyPatch,
    *,
    raise_on: set[str] | None = None,
) -> list[StubSystem]:
    created: list[StubSystem] = []

    def factory() -> StubSystem:
        stub = StubSystem(raise_on=raise_on)
        created.append(stub)
        return stub

    monkeypatch.setattr(main, "PoliceSystem", factory)
    return created


@pytest.mark.parametrize(
    ("command", "expected"),
    [
        ("statement add \"Theft\" A 0 1", ("create_statement", ("Theft", "A", 0, 1), {})),
        ("statement delete 3", ("delete_statement", (3,), {})),
        ("statement list", ("show_statements", (), {})),
        ("citizen add \"John Doe\" --zone A", ("add_citizen", ("John Doe",), {"zone": "A"})),
        ("citizen add \"Mary\" -z B", ("add_citizen", ("Mary",), {"zone": "B"})),
        ("citizen delete 2", ("delete_citizen", (2,), {})),
        ("citizen list", ("show_citizens", (), {})),
        ("police hire Smith A", ("hire_policeman", ("Smith", "A"), {})),
        ("police fire Smith", ("fire_policeman", ("Smith",), {})),
        ("police add-zone Center", ("add_zone", ("Center",), {})),
        ("police list", ("show_policemen", (), {})),
        ("police info", ("show_info", (), {})),
        ("police recover", ("recover_policemen", (), {})),
        ("police relocate 0 1 B", ("relocate_policemen", ([0, 1], "B"), {})),
        ("investigate", ("investigate_crimes", (), {"do_arrest": False})),
        ("investigate --arrest", ("investigate_crimes", (), {"do_arrest": True})),
        ("history show", ("show_history", (), {})),
        ("history clear", ("clear_history", (), {})),
        ("law add 10 2 Fraud", ("add_law", (10, 2, "Fraud"), {})),
        ("law list", ("show_laws", (), {})),
        ("save", ("save_data", (), {})),
    ],
)
def test_interactive_dispatches_commands(
    monkeypatch: pytest.MonkeyPatch,
    command: str,
    expected: tuple[str, tuple, dict],
) -> None:
    system = StubSystem()
    _run_interactive(monkeypatch, system, [command, "exit"])
    assert expected in system.calls


def test_interactive_handles_usage_unknown_and_generic_error(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    system = StubSystem()
    _run_interactive(
        monkeypatch,
        system,
        [
            "statement",
            "statement add one",
            "statement delete",
            "citizen",
            "citizen add",
            "citizen delete",
            "police",
            "police hire",
            "police fire",
            "police add-zone",
            "police relocate 1",
            "history",
            "law",
            "law add 1 2",
            "statement add Test A a b",
            "unknown-cmd",
            "exit",
        ],
    )
    out = capsys.readouterr().out
    assert "Usage: statement <add|delete|list>" in out
    assert "Usage: citizen <add|delete|list>" in out
    assert "Usage: police <hire|fire|add-zone|list|info|relocate> [args...]" in out
    assert "Usage: history <show|clear>" in out
    assert "Usage: law <add|list> [args...]" in out
    assert "Unknown command: unknown-cmd" in out
    assert "✗ Error:" in out


def test_interactive_handles_keyboard_interrupt(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    system = StubSystem()
    _run_interactive(monkeypatch, system, [KeyboardInterrupt(), "exit"])
    out = capsys.readouterr().out
    assert "Use 'exit' or 'save' to save and quit" in out


def test_interactive_handles_method_exception(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    system = StubSystem(raise_on={"show_laws"})
    _run_interactive(monkeypatch, system, ["law list", "exit"])
    out = capsys.readouterr().out
    assert "✗ Error: boom" in out


def test_print_help_renders(capsys: pytest.CaptureFixture[str]) -> None:
    main.print_help()
    out = capsys.readouterr().out
    assert "POLICE MANAGEMENT SYSTEM - HELP" in out
    assert "CITIZEN COMMANDS" in out
    assert "SYSTEM:" in out


@pytest.mark.parametrize(
    ("argv", "expected_call"),
    [
        (["prog", "statement", "add", "Theft", "A", "1", "2"], ("create_statement", ("Theft", "A", 1, 2), {})),
        (["prog", "statement", "delete", "3"], ("delete_statement", (3,), {})),
        (["prog", "statement", "list"], ("show_statements", (), {})),
        (["prog", "citizen", "add", "John", "--zone", "A"], ("add_citizen", ("John",), {"zone": "A"})),
        (["prog", "citizen", "delete", "1"], ("delete_citizen", (1,), {})),
        (["prog", "citizen", "list"], ("show_citizens", (), {})),
        (["prog", "police", "hire", "Smith", "A"], ("hire_policeman", ("Smith", "A"), {})),
        (["prog", "police", "fire", "Smith"], ("fire_policeman", ("Smith",), {})),
        (["prog", "police", "add-zone", "A"], ("add_zone", ("A",), {})),
        (["prog", "police", "list"], ("show_policemen", (), {})),
        (["prog", "police", "info"], ("show_info", (), {})),
        (["prog", "police", "recover"], ("recover_policemen", (), {})),
        (["prog", "police", "relocate", "0", "1", "B"], ("relocate_policemen", ([0, 1], "B"), {})),
        (["prog", "investigate", "--arrest"], ("investigate_crimes", (), {"do_arrest": True})),
        (["prog", "history", "show"], ("show_history", (), {})),
        (["prog", "history", "clear"], ("clear_history", (), {})),
        (["prog", "law", "add", "100", "5", "Violence"], ("add_law", (100, 5, "Violence"), {})),
        (["prog", "law", "list"], ("show_laws", (), {})),
    ],
)
def test_main_cli_dispatches(
    monkeypatch: pytest.MonkeyPatch,
    argv: list[str],
    expected_call: tuple[str, tuple, dict],
) -> None:
    created = _install_stub_factory(monkeypatch)
    monkeypatch.setattr(main.sys, "argv", argv)
    main.main()
    stub = created[0]
    assert expected_call in stub.calls
    assert ("save_data", (), {}) in stub.calls


def test_main_cli_save_and_exit_commands(monkeypatch: pytest.MonkeyPatch) -> None:
    created = _install_stub_factory(monkeypatch)
    monkeypatch.setattr(main.sys, "argv", ["prog", "save"])
    main.main()
    assert created[0].calls.count(("save_data", (), {})) == 1

    created = _install_stub_factory(monkeypatch)
    monkeypatch.setattr(main.sys, "argv", ["prog", "exit"])
    main.main()
    assert created[0].calls.count(("save_data", (), {})) == 1


def test_main_runs_interactive_when_no_cli_args(monkeypatch: pytest.MonkeyPatch) -> None:
    created = _install_stub_factory(monkeypatch)
    called: dict[str, object] = {}

    def fake_interactive(system: object) -> None:
        called["system"] = system

    monkeypatch.setattr(main, "interactive_mode", fake_interactive)
    monkeypatch.setattr(main.sys, "argv", ["prog"])
    main.main()
    assert called["system"] is created[0]


def test_main_cli_exits_with_error_when_handler_fails(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _install_stub_factory(monkeypatch, raise_on={"show_laws"})
    monkeypatch.setattr(main.sys, "argv", ["prog", "law", "list"])
    with pytest.raises(SystemExit) as exc:
        main.main()
    assert exc.value.code == 1
    err = capsys.readouterr().err
    assert "✗ Error: boom" in err


def test_load_data_and_save_data_roundtrip(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    monkeypatch.setattr(main, "DATA_DIR", data_dir)

    source_police = Police()
    source_police.add_zone("A")
    source_objects = {
        "police": source_police,
        "applications": [],
        "history": ["event"],
        "citizens": [Citizen("John")],
        "laws": [Law(10, 2, "desc")],
        "security": Security(2.0),
    }

    for key, filename in main.DATA_FILES.items():
        with open(data_dir / filename, "wb") as fh:
            pickle.dump(source_objects[key], fh)

    system = main.PoliceSystem()
    out = capsys.readouterr().out
    assert "Loaded" in out
    assert system.history == ["event"]

    system.save_data()
    for filename in main.DATA_FILES.values():
        assert (data_dir / filename).exists()


def test_police_system_statement_and_citizen_branches(
    real_system: main.PoliceSystem,
    capsys: pytest.CaptureFixture[str],
) -> None:
    real_system.create_statement("x", "A", 0, 0)
    real_system.laws = []
    real_system.citizens = [Citizen("Temp")]
    real_system.create_statement("x", "A", 0, 0)

    real_system.laws = [Law(1, 1, "l")]
    real_system.citizens = [Citizen("John")]
    real_system.create_statement("x", "A", 0, 0)

    real_system.police.add_zone("A")
    real_system.create_statement("x", "A", 99, 0)
    real_system.create_statement("theft", "A", 0, 0)
    real_system.show_statements()
    real_system.delete_statement(0)
    real_system.delete_statement(99)

    real_system.show_citizens()
    real_system.add_citizen("Ghost", zone="Missing")
    real_system.add_citizen("Mary", zone="A")
    real_system.show_citizens()
    real_system.delete_citizen(0)
    real_system.delete_citizen(99)

    out = capsys.readouterr().out
    assert "No citizens registered" in out
    assert "No laws defined" in out
    assert "Zone 'A' does not exist" in out
    assert "Crime report filed successfully" in out
    assert "Invalid application index" in out
    assert "Invalid citizen index" in out
    assert "Zone 'Missing' does not exist" in out


def test_police_system_police_and_info_branches(
    real_system: main.PoliceSystem,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    real_system.show_policemen()
    real_system.show_info()
    real_system.hire_policeman("Smith", "A")
    real_system.add_zone("A")
    real_system.add_zone("A")
    real_system.hire_policeman("Smith", "A")
    real_system.show_policemen()
    real_system.show_info()
    real_system.fire_policeman("Smith")
    real_system.fire_policeman("Unknown")

    real_system.add_zone("B")
    real_system.hire_policeman("Miller", "A")
    real_system.relocate_policemen([0], "B")
    real_system.relocate_policemen([999], "B")
    real_system.relocate_policemen([0], "Missing")

    officer = real_system.police.get_policemen()[0]
    monkeypatch.setattr(officer, "_is_resting", True)
    real_system.recover_policemen()
    real_system.recover_policemen()

    out = capsys.readouterr().out
    assert "No policemen hired" in out
    assert "No zones registered" in out
    assert "does not exist. Create it first" in out
    assert "Zone 'A' created" in out
    assert "Error: Zone 'A' already exists" in out
    assert "Officer Smith hired" in out
    assert "Officer Smith fired" in out
    assert "Policeman 'Unknown' not found" in out
    assert "Officers relocated to zone B" in out
    assert "Invalid policeman index" in out
    assert "Target zone 'Missing' does not exist" in out
    assert "officer(s) recovered from rest" in out or "No officers need recovery" in out


def test_police_system_investigation_history_and_laws(
    real_system: main.PoliceSystem,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    real_system.investigate_crimes()

    real_system.police.add_zone("A")
    citizen = Citizen("John")
    real_system.citizens = [citizen]
    law = Law(2, 2, "test")
    real_system.laws = [law]
    real_system.applications = [Crime(citizen, "case", "A", law)]

    monkeypatch.setattr(Investigation, "investigate_all", lambda self: [])
    real_system.investigate_crimes()

    monkeypatch.setattr(Investigation, "investigate_all", lambda self: [(real_system.applications[0], 2)])
    real_system.investigate_crimes(do_arrest=False)

    original_cleanup = real_system._perform_arrests_and_cleanup
    called: dict[str, bool] = {"done": False}

    def fake_cleanup() -> None:
        called["done"] = True

    monkeypatch.setattr(real_system, "_perform_arrests_and_cleanup", fake_cleanup)
    real_system.investigate_crimes(do_arrest=True)
    assert called["done"] is True
    monkeypatch.setattr(real_system, "_perform_arrests_and_cleanup", original_cleanup)

    # Cover failed arrest branch and delegate method.
    real_system.police.hire(Policeman("Smith", "A"), "A")
    real_system.police.get_policemen()[0].assign_crime((real_system.applications[0], 2))
    monkeypatch.setattr(real_system.police.get_policemen()[0], "arrest", lambda: False)
    monkeypatch.setattr(real_system, "_update_security", lambda: None)
    real_system._perform_arrests_and_cleanup()
    real_system.arrest_criminals()

    real_system.show_history()
    real_system.history.append("event")
    real_system.show_history()
    real_system.clear_history()

    real_system.laws = []
    real_system.show_laws()
    real_system.add_law(100, 3, "fraud")
    real_system.show_laws()

    out = capsys.readouterr().out
    assert "No crimes to investigate" in out
    assert "Investigation inconclusive" in out
    assert "Investigation completed" in out
    assert "Attempting arrests" in out
    assert "failed to arrest suspect" in out
    assert "History is empty" in out
    assert "History cleared" in out
    assert "No laws defined" in out
    assert "Law added" in out
