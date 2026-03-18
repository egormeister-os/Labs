from __future__ import annotations

from datetime import date

import pytest
from PyQt5.QtWidgets import QMessageBox

from app.models import SearchCriteria, ValidationError
from app.views.dialogs.criteria_form import CriteriaFormWidget
from app.views.dialogs.delete_dialog import DeleteDialog
from app.views.dialogs.record_dialog import RecordDialog
from app.views.dialogs.search_dialog import SearchDialog
from app.views.widgets import PaginationWidget, RecordTableWidget, RecordTreeWidget


@pytest.fixture
def messagebox_spy(monkeypatch):
    calls = {"warning": [], "information": [], "question": []}

    def fake_warning(*args, **kwargs):
        calls["warning"].append((args, kwargs))
        return QMessageBox.Ok

    def fake_information(*args, **kwargs):
        calls["information"].append((args, kwargs))
        return QMessageBox.Ok

    def fake_question(*args, **kwargs):
        calls["question"].append((args, kwargs))
        return QMessageBox.Yes

    monkeypatch.setattr(QMessageBox, "warning", fake_warning)
    monkeypatch.setattr(QMessageBox, "information", fake_information)
    monkeypatch.setattr(QMessageBox, "question", fake_question)
    return calls


def test_pagination_widget_updates_state_and_emits_signals(qapp):
    widget = PaginationWidget()
    requested_pages = []
    page_sizes = []
    widget.page_requested.connect(requested_pages.append)
    widget.page_size_changed.connect(page_sizes.append)

    widget.update_state(current_page=2, page_size=20, current_page_count=20, total_count=45, total_pages=3)

    assert "Страница 2 из 3" in widget.info_label.text()
    assert widget.first_button.isEnabled() is True
    assert widget.previous_button.isEnabled() is True
    assert widget.next_button.isEnabled() is True
    assert widget.last_button.isEnabled() is True

    widget.previous_button.click()
    widget.next_button.click()
    widget.first_button.click()
    widget.last_button.click()
    widget.page_size_combo.setCurrentText("50")

    assert requested_pages == [1, 3, 1, 3]
    assert page_sizes == [50]

    widget.update_state(current_page=1, page_size=5, current_page_count=0, total_count=0, total_pages=1)
    assert widget.first_button.isEnabled() is False
    assert widget.next_button.isEnabled() is False


def test_record_table_and_tree_widgets_render_records(qapp, sample_records):
    table = RecordTableWidget()
    table.set_records(sample_records[:2])
    assert table.rowCount() == 2
    assert table.item(0, 0).text() == sample_records[0].tournament_name

    tree = RecordTreeWidget()
    tree.set_records(sample_records[:1])
    assert tree.topLevelItemCount() == 1
    root = tree.topLevelItem(0)
    assert root.text(0) == "Запись 1"
    assert root.childCount() == 6
    assert root.child(0).text(0) == "Название турнира"


def test_criteria_form_widget_to_criteria_and_reset(qapp):
    widget = CriteriaFormWidget(["Tennis", "Football"])
    widget.tournament_name_edit.setText("  Кубок  ")
    widget.date_checkbox.setChecked(True)
    widget.date_edit.setDate(widget.date_edit.date().fromString("2025-02-10", "yyyy-MM-dd"))
    widget.sport_combo.setCurrentText("Football")
    widget.winner_name_fragment_edit.setText("  Иван ")
    widget.min_prize_checkbox.setChecked(True)
    widget.min_prize_spin.setValue(100)
    widget.max_earnings_checkbox.setChecked(True)
    widget.max_earnings_spin.setValue(200)

    criteria = widget.to_criteria()
    assert criteria.tournament_name == "Кубок"
    assert criteria.sport_name == "Football"
    assert criteria.winner_name_fragment == "Иван"
    assert criteria.min_prize_amount == 100
    assert criteria.max_winner_earnings == 200

    widget.reset()
    assert widget.tournament_name_edit.text() == ""
    assert widget.date_checkbox.isChecked() is False
    assert widget.sport_combo.currentText() == ""
    assert widget.min_prize_spin.value() == 0


def test_criteria_form_widget_rejects_invalid_range(qapp):
    widget = CriteriaFormWidget(["Tennis"])
    widget.min_prize_checkbox.setChecked(True)
    widget.min_prize_spin.setValue(1000)
    widget.max_prize_checkbox.setChecked(True)
    widget.max_prize_spin.setValue(100)

    with pytest.raises(ValidationError):
        widget.to_criteria()


def test_record_dialog_accepts_valid_input_and_shows_warning_for_invalid(qapp, messagebox_spy):
    dialog = RecordDialog(["Tennis"])
    dialog.tournament_name_edit.setText("Турнир")
    dialog.sport_combo.setCurrentText("Tennis")
    dialog.winner_name_edit.setText("Победитель")
    dialog.prize_amount_spin.setValue(1500)
    dialog.accept()

    assert dialog.record_input is not None
    assert dialog.record_input.prize_amount == 1500
    assert dialog.winner_earnings_edit.text() == "900.00"

    invalid_dialog = RecordDialog(["Tennis"])
    invalid_dialog.accept()
    assert invalid_dialog.record_input is None
    assert len(messagebox_spy["warning"]) == 1


def test_search_dialog_runs_search_resets_and_handles_invalid_form(qapp, controller, monkeypatch, messagebox_spy):
    dialog = SearchDialog(controller)
    dialog.criteria_form.tournament_name_edit.setText("Кубок")
    dialog._run_search_from_form()

    assert "Найдено записей: 2." in dialog.summary_label.text()
    assert dialog.results_table.rowCount() == 2

    dialog._change_page_size(5)
    assert dialog.page_size == 5

    dialog._reset_form()
    assert dialog.current_criteria == SearchCriteria()
    assert dialog.results_table.rowCount() == 3

    monkeypatch.setattr(
        dialog.criteria_form,
        "to_criteria",
        lambda: (_ for _ in ()).throw(ValidationError("bad search")),
    )
    dialog._run_search_from_form()
    assert len(messagebox_spy["warning"]) >= 1


def test_delete_dialog_handles_empty_invalid_zero_and_positive_deletions(
    qapp,
    controller,
    monkeypatch,
    messagebox_spy,
):
    empty_dialog = DeleteDialog(controller)
    empty_dialog._delete_records()
    assert len(messagebox_spy["warning"]) == 1

    invalid_dialog = DeleteDialog(controller)
    monkeypatch.setattr(
        invalid_dialog.criteria_form,
        "to_criteria",
        lambda: (_ for _ in ()).throw(ValidationError("bad delete")),
    )
    invalid_dialog._delete_records()
    assert len(messagebox_spy["warning"]) == 2

    no_match_dialog = DeleteDialog(controller)
    no_match_dialog.criteria_form.tournament_name_edit.setText("Не существует")
    no_match_dialog._delete_records()
    assert no_match_dialog.deleted_count == 0
    assert len(messagebox_spy["information"]) == 1

    delete_dialog = DeleteDialog(controller)
    delete_dialog.criteria_form.sport_combo.setCurrentText("Football")
    delete_dialog._delete_records()
    assert delete_dialog.deleted_count == 1
    assert len(messagebox_spy["information"]) == 2
    assert controller.get_records_page(1, 10).total_count == 2
