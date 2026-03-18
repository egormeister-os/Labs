from __future__ import annotations

from PyQt5.QtCore import QDate
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QDoubleSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.models import SearchCriteria


class CriteriaFormWidget(QWidget):
    def __init__(self, sports: list[str] | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.tournament_name_edit = QLineEdit()
        self.date_checkbox = QCheckBox("Искать/удалять по дате")
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setEnabled(False)
        self.date_checkbox.toggled.connect(self.date_edit.setEnabled)

        self.sport_combo = QComboBox()
        self.sport_combo.addItem("")
        self.winner_name_fragment_edit = QLineEdit()

        self.min_prize_checkbox, self.min_prize_spin, min_prize_widget = self._build_optional_spinbox("От")
        self.max_prize_checkbox, self.max_prize_spin, max_prize_widget = self._build_optional_spinbox("До")
        self.min_earnings_checkbox, self.min_earnings_spin, min_earnings_widget = self._build_optional_spinbox("От")
        self.max_earnings_checkbox, self.max_earnings_spin, max_earnings_widget = self._build_optional_spinbox("До")

        if sports:
            self.refresh_sports(sports)

        main_layout = QVBoxLayout(self)
        general_form = QFormLayout()
        general_form.addRow("Название турнира:", self.tournament_name_edit)

        date_widget = QWidget()
        date_layout = QHBoxLayout(date_widget)
        date_layout.setContentsMargins(0, 0, 0, 0)
        date_layout.addWidget(self.date_checkbox)
        date_layout.addWidget(self.date_edit)
        general_form.addRow("Дата проведения:", date_widget)
        general_form.addRow("Вид спорта:", self.sport_combo)
        general_form.addRow("Фрагмент ФИО победителя:", self.winner_name_fragment_edit)

        prize_group = QGroupBox("Размер призовых турнира")
        prize_layout = QGridLayout(prize_group)
        prize_layout.addWidget(min_prize_widget, 0, 0)
        prize_layout.addWidget(max_prize_widget, 0, 1)

        earnings_group = QGroupBox("Заработок победителя")
        earnings_layout = QGridLayout(earnings_group)
        earnings_layout.addWidget(min_earnings_widget, 0, 0)
        earnings_layout.addWidget(max_earnings_widget, 0, 1)

        hint_label = QLabel(
            "Для ФИО можно указывать только часть строки, например имя победителя."
        )
        hint_label.setWordWrap(True)

        main_layout.addLayout(general_form)
        main_layout.addWidget(prize_group)
        main_layout.addWidget(earnings_group)
        main_layout.addWidget(hint_label)

    def refresh_sports(self, sports: list[str]) -> None:
        current_value = self.sport_combo.currentText()
        self.sport_combo.blockSignals(True)
        self.sport_combo.clear()
        self.sport_combo.addItem("")
        self.sport_combo.addItems(sports)
        index = self.sport_combo.findText(current_value)
        if index >= 0:
            self.sport_combo.setCurrentIndex(index)
        self.sport_combo.blockSignals(False)

    def reset(self) -> None:
        self.tournament_name_edit.clear()
        self.date_checkbox.setChecked(False)
        self.date_edit.setDate(QDate.currentDate())
        self.sport_combo.setCurrentIndex(0)
        self.winner_name_fragment_edit.clear()

        for checkbox, spinbox in (
            (self.min_prize_checkbox, self.min_prize_spin),
            (self.max_prize_checkbox, self.max_prize_spin),
            (self.min_earnings_checkbox, self.min_earnings_spin),
            (self.max_earnings_checkbox, self.max_earnings_spin),
        ):
            checkbox.setChecked(False)
            spinbox.setValue(0)

    def to_criteria(self) -> SearchCriteria:
        return SearchCriteria(
            tournament_name=self.tournament_name_edit.text(),
            event_date=self.date_edit.date().toPyDate() if self.date_checkbox.isChecked() else None,
            sport_name=self.sport_combo.currentText(),
            winner_name_fragment=self.winner_name_fragment_edit.text(),
            min_prize_amount=self.min_prize_spin.value() if self.min_prize_checkbox.isChecked() else None,
            max_prize_amount=self.max_prize_spin.value() if self.max_prize_checkbox.isChecked() else None,
            min_winner_earnings=(
                self.min_earnings_spin.value() if self.min_earnings_checkbox.isChecked() else None
            ),
            max_winner_earnings=(
                self.max_earnings_spin.value() if self.max_earnings_checkbox.isChecked() else None
            ),
        ).normalized()

    @staticmethod
    def _build_optional_spinbox(title: str):
        checkbox = QCheckBox(title)
        spinbox = QDoubleSpinBox()
        spinbox.setDecimals(2)
        spinbox.setRange(0, 1_000_000_000)
        spinbox.setSingleStep(1000)
        spinbox.setEnabled(False)
        checkbox.toggled.connect(spinbox.setEnabled)

        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(checkbox)
        layout.addWidget(spinbox)
        return checkbox, spinbox, widget
