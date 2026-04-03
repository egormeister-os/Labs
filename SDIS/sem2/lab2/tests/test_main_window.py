from __future__ import annotations

from datetime import date
from pathlib import Path

from PyQt5.QtGui import QCloseEvent
from PyQt5.QtWidgets import QMessageBox

from app.models import TournamentRecordInput, ValidationError
from app.views.main_window import MainWindow


def test_main_window_refresh_and_switch_view(qapp, controller):
    window = MainWindow(controller)

    assert window.table_widget.rowCount() == 3
    assert "Показано 3 из 3." in window.page_title_label.text()

    window._set_view_mode(1)
    assert window.stacked_widget.currentIndex() == 1

    window._change_page_size(2)
    assert window.page_size == 2
    assert window.table_widget.rowCount() == 2

    assert window._ensure_suffix(Path("file"), ".xml") == Path("file.xml")
    assert window._ensure_suffix(Path("file.db"), ".db") == Path("file.db")

    window.close()


def test_main_window_open_add_search_and_delete_dialogs(qapp, controller, monkeypatch):
    import app.views.main_window as main_window_module

    added_inputs = []
    original_add_record = controller.add_record

    def capture_add(record_input):
        added_inputs.append(record_input)
        return original_add_record(record_input)

    monkeypatch.setattr(controller, "add_record", capture_add)

    class FakeRecordDialog:
        def __init__(self, sports, parent):
            self.record_input = TournamentRecordInput(
                tournament_name="Добавленный турнир",
                event_date=date(2025, 5, 5),
                sport_name="Chess",
                winner_full_name="Тестовый Победитель",
                prize_amount=2222,
            )

        def exec_(self):
            return 1

    search_executed = []

    class FakeSearchDialog:
        def __init__(self, controller_arg, parent):
            search_executed.append(controller_arg)

        def exec_(self):
            search_executed.append("exec")
            return 1

    class FakeDeleteDialog:
        def __init__(self, controller_arg, parent):
            self.controller_arg = controller_arg

        def exec_(self):
            return 1

    window = MainWindow(controller)
    monkeypatch.setattr(main_window_module, "RecordDialog", FakeRecordDialog)
    monkeypatch.setattr(main_window_module, "SearchDialog", FakeSearchDialog)
    monkeypatch.setattr(main_window_module, "DeleteDialog", FakeDeleteDialog)

    refresh_calls = []
    original_refresh = window.refresh_records

    def capture_refresh(page):
        refresh_calls.append(page)
        return original_refresh(page)

    monkeypatch.setattr(window, "refresh_records", capture_refresh)

    window._open_add_dialog()
    window._open_search_dialog()
    window._open_delete_dialog()

    assert len(added_inputs) == 1
    assert search_executed == [controller, "exec"]
    assert refresh_calls[-2:] == [1, window.current_page]
    assert controller.get_records_page(1, 10).total_count == 4

    window.close()


def test_main_window_handles_add_record_validation_error(qapp, controller, monkeypatch):
    import app.views.main_window as main_window_module

    warnings = []

    class FakeRecordDialog:
        def __init__(self, sports, parent):
            self.record_input = TournamentRecordInput(
                tournament_name="Турнир",
                event_date=date(2025, 1, 1),
                sport_name="Tennis",
                winner_full_name="Игрок",
                prize_amount=100,
            )

        def exec_(self):
            return 1

    def fake_warning(*args, **kwargs):
        warnings.append((args, kwargs))
        return QMessageBox.Ok

    monkeypatch.setattr(main_window_module, "RecordDialog", FakeRecordDialog)
    monkeypatch.setattr(QMessageBox, "warning", fake_warning)
    monkeypatch.setattr(
        controller,
        "add_record",
        lambda record_input: (_ for _ in ()).throw(ValidationError("broken")),
    )

    window = MainWindow(controller)
    window._open_add_dialog()

    assert len(warnings) == 1
    window.close()


def test_main_window_file_operations_and_error_paths(qapp, controller, monkeypatch, tmp_path):
    import app.views.main_window as main_window_module

    warnings = []

    def fake_warning(*args, **kwargs):
        warnings.append((args, kwargs))
        return QMessageBox.Ok

    monkeypatch.setattr(QMessageBox, "warning", fake_warning)
    monkeypatch.setattr(QMessageBox, "question", lambda *args, **kwargs: QMessageBox.Yes)

    window = MainWindow(controller)

    export_path = tmp_path / "exported"
    monkeypatch.setattr(
        main_window_module.QFileDialog,
        "getSaveFileName",
        lambda *args, **kwargs: (str(export_path), "XML"),
    )
    window._export_xml()
    assert (tmp_path / "exported.xml").exists()

    import_source = tmp_path / "import_source.xml"
    controller.export_to_xml(import_source)
    monkeypatch.setattr(
        main_window_module.QFileDialog,
        "getOpenFileName",
        lambda *args, **kwargs: (str(import_source), "XML"),
    )
    window._import_xml()
    assert controller.get_records_page(1, 10).total_count == 3

    db_target = tmp_path / "saved_db"
    monkeypatch.setattr(
        main_window_module.QFileDialog,
        "getSaveFileName",
        lambda *args, **kwargs: (str(db_target), "SQLite"),
    )
    window._save_database_as()
    assert controller.current_database_path == tmp_path / "saved_db.db"

    second_db = tmp_path / "second.db"
    monkeypatch.setattr(
        main_window_module.QFileDialog,
        "getOpenFileNames",
        lambda *args, **kwargs: ([str(second_db)], "SQLite"),
    )
    window._open_database()
    assert controller.current_database_path == second_db

    monkeypatch.setattr(
        main_window_module.QFileDialog,
        "getSaveFileName",
        lambda *args, **kwargs: (str(tmp_path / "bad_export.xml"), "XML"),
    )
    monkeypatch.setattr(
        controller,
        "export_to_xml",
        lambda path: (_ for _ in ()).throw(RuntimeError("export error")),
    )
    window._export_xml()

    monkeypatch.setattr(
        controller,
        "save_database_as",
        lambda path: (_ for _ in ()).throw(RuntimeError("save error")),
    )
    monkeypatch.setattr(
        main_window_module.QFileDialog,
        "getSaveFileName",
        lambda *args, **kwargs: (str(tmp_path / "bad_save.db"), "SQLite"),
    )
    window._save_database_as()

    monkeypatch.setattr(
        controller,
        "open_databases",
        lambda paths: (_ for _ in ()).throw(RuntimeError("open error")),
    )
    monkeypatch.setattr(
        main_window_module.QFileDialog,
        "getOpenFileNames",
        lambda *args, **kwargs: ([str(tmp_path / "bad_open.db")], "SQLite"),
    )
    window._open_database()

    monkeypatch.setattr(
        controller,
        "import_from_xml",
        lambda path: (_ for _ in ()).throw(RuntimeError("import error")),
    )
    monkeypatch.setattr(
        main_window_module.QFileDialog,
        "getOpenFileName",
        lambda *args, **kwargs: (str(import_source), "XML"),
    )
    window._import_xml()

    assert len(warnings) == 4
    window.close()


def test_main_window_open_multiple_databases_shows_unique_records(
    qapp,
    controller,
    monkeypatch,
    tmp_path,
    make_input,
):
    import app.views.main_window as main_window_module

    duplicate_record = make_input(
        tournament_name="Кубок Минска",
        event_date=date(2025, 1, 10),
        sport_name="Tennis",
        winner_full_name="Иванов Иван Иванович",
        prize_amount=1000.0,
    )
    extra_record = make_input(
        tournament_name="Гран-при Витебска",
        event_date=date(2025, 4, 5),
        sport_name="Basketball",
        winner_full_name="Ковалев Андрей Сергеевич",
        prize_amount=4100.0,
    )

    extra_database = tmp_path / "extra.db"
    extra_controller = type(controller)(extra_database)
    try:
        extra_controller.add_record(duplicate_record)
        extra_controller.add_record(extra_record)
    finally:
        extra_controller.close()

    window = MainWindow(controller)
    monkeypatch.setattr(
        main_window_module.QFileDialog,
        "getOpenFileNames",
        lambda *args, **kwargs: (
            [str(controller.current_database_path), str(extra_database)],
            "SQLite",
        ),
    )

    window._open_database()

    assert window.table_widget.rowCount() == 4
    assert "Открыто БД: 2." in window.page_title_label.text()
    assert "extra.db" in window.statusBar().currentMessage()
    window.close()


def test_main_window_import_cancel_and_close_event(qapp, controller, monkeypatch, tmp_path):
    import app.views.main_window as main_window_module

    close_calls = []
    monkeypatch.setattr(QMessageBox, "question", lambda *args, **kwargs: QMessageBox.No)
    monkeypatch.setattr(
        main_window_module.QFileDialog,
        "getOpenFileName",
        lambda *args, **kwargs: (str(tmp_path / "ignored.xml"), "XML"),
    )
    monkeypatch.setattr(controller, "close", lambda: close_calls.append("closed"))

    window = MainWindow(controller)
    window._import_xml()
    window.closeEvent(QCloseEvent())

    assert close_calls == ["closed"]
