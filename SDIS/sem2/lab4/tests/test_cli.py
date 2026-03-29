from __future__ import annotations

import argparse

from app.cli import main as cli
from app.services import PoliceSystem


def test_print_helpers_and_help(capsys, service):
    cli._print_result(service.save_data())
    cli._print_indexed([], "Empty list")
    cli._print_zone_info(service)
    cli.print_help()

    output = capsys.readouterr().out
    assert "Data saved successfully" in output
    assert "Empty list" in output
    assert "No zones registered" in output
    assert "POLICE MANAGEMENT SYSTEM - HELP" in output


def test_dispatch_paths(capsys, seeded_service):
    cli.dispatch(seeded_service, argparse.Namespace(command="save"))
    cli.dispatch(seeded_service, argparse.Namespace(command="exit"))
    cli.dispatch(seeded_service, argparse.Namespace(command="statement", subcommand="list"))
    cli.dispatch(seeded_service, argparse.Namespace(command="citizen", subcommand="list"))
    cli.dispatch(seeded_service, argparse.Namespace(command="police", subcommand="list"))
    cli.dispatch(seeded_service, argparse.Namespace(command="police", subcommand="info"))
    cli.dispatch(seeded_service, argparse.Namespace(command="history", subcommand="show"))
    cli.dispatch(seeded_service, argparse.Namespace(command="law", subcommand="list"))

    output = capsys.readouterr().out
    assert "Goodbye!" in output
    assert "Bike theft" in output
    assert "John Smith" in output
    assert "Zone: Downtown" in output
    assert "Article" in output


def test_dispatch_mutating_commands(capsys, service):
    cli.dispatch(service, argparse.Namespace(command="police", subcommand="add-zone", zone="Downtown"))
    cli.dispatch(service, argparse.Namespace(command="citizen", subcommand="add", name="John Smith", zone="Downtown"))
    cli.dispatch(service, argparse.Namespace(command="law", subcommand="add", article=808, severity=3, desc="Fraud"))
    cli.dispatch(
        service,
        argparse.Namespace(
            command="statement",
            subcommand="add",
            description="Bike theft",
            zone="Downtown",
            suspect_idx=0,
            law_idx=0,
        ),
    )
    cli.dispatch(service, argparse.Namespace(command="investigate", arrest=False))
    cli.dispatch(service, argparse.Namespace(command="history", subcommand="clear"))

    output = capsys.readouterr().out
    assert "Zone 'Downtown' created" in output
    assert "Citizen 'John Smith' added" in output
    assert "Law added" in output


def test_interactive_mode_and_main(monkeypatch, capsys, storage):
    service = PoliceSystem(storage=storage)
    monkeypatch.setattr(cli, "PoliceSystem", lambda: service)

    answers = iter(["help", "exit"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))
    cli.interactive_mode(service)
    output = capsys.readouterr().out
    assert "POLICE MANAGEMENT SYSTEM" in output
    assert "Goodbye!" in output

    monkeypatch.setattr(cli.sys, "argv", ["run_cli.py", "save"])
    cli.main()
    output = capsys.readouterr().out
    assert "Data saved successfully" in output
