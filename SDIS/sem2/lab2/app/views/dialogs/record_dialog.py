from __future__ import annotations

from PyQt5.QtCore import QDate
from PyQt5.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
)

from app.models import TournamentRecordInput, ValidationError, compute_winner_earnings


class RecordDialog(QDialog):
    def __init__(self, sports: list[str], parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Добавление записи")
        self.setModal(True)
        self.record_input: TournamentRecordInput | None = None

        self.tournament_name_edit = QLineEdit()
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.sport_combo = QComboBox()
        self.sport_combo.setEditable(True)
        self.sport_combo.addItems(sports)
        self.winner_name_edit = QLineEdit()
        self.prize_amount_spin = QDoubleSpinBox()
        self.prize_amount_spin.setRange(0, 1_000_000_000)
        self.prize_amount_spin.setDecimals(2)
        self.prize_amount_spin.setSingleStep(1000)
        self.winner_earnings_edit = QLineEdit()
        self.winner_earnings_edit.setReadOnly(True)

        form_layout = QFormLayout()
        form_layout.addRow("Название турнира:", self.tournament_name_edit)
        form_layout.addRow("Дата проведения:", self.date_edit)
        form_layout.addRow("Вид спорта:", self.sport_combo)
        form_layout.addRow("ФИО победителя:", self.winner_name_edit)
        form_layout.addRow("Размер призовых:", self.prize_amount_spin)
        form_layout.addRow("Заработок победителя (60%):", self.winner_earnings_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form_layout)
        layout.addWidget(buttons)

        self.prize_amount_spin.valueChanged.connect(self._update_earnings_preview)
        self._update_earnings_preview()

    def accept(self) -> None:
        try:
            self.record_input = TournamentRecordInput(
                tournament_name=self.tournament_name_edit.text(),
                event_date=self.date_edit.date().toPyDate(),
                sport_name=self.sport_combo.currentText(),
                winner_full_name=self.winner_name_edit.text(),
                prize_amount=self.prize_amount_spin.value(),
            ).normalized()
        except ValidationError as error:
            QMessageBox.warning(self, "Ошибка ввода", str(error))
            return

        super().accept()

    def _update_earnings_preview(self) -> None:
        earnings = compute_winner_earnings(self.prize_amount_spin.value())
        self.winner_earnings_edit.setText(f"{earnings:,.2f}".replace(",", " "))
