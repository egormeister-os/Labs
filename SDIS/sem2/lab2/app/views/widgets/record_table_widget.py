from __future__ import annotations

from PyQt5.QtWidgets import QAbstractItemView, QHeaderView, QTableWidget, QTableWidgetItem

from app.models import TournamentRecord


class RecordTableWidget(QTableWidget):
    HEADERS = [
        "Название турнира",
        "Дата проведения",
        "Вид спорта",
        "ФИО победителя",
        "Размер призовых",
        "Заработок победителя",
    ]

    def __init__(self, parent=None) -> None:
        super().__init__(0, len(self.HEADERS), parent)
        self.setHorizontalHeaderLabels(self.HEADERS)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def set_records(self, records: list[TournamentRecord]) -> None:
        self.setRowCount(len(records))
        for row_index, record in enumerate(records):
            for column_index, value in enumerate(record.as_tuple()):
                self.setItem(row_index, column_index, QTableWidgetItem(value))
        self.resizeRowsToContents()
