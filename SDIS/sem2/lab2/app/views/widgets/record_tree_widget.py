from __future__ import annotations

from PyQt5.QtWidgets import QHeaderView, QTreeWidget, QTreeWidgetItem

from app.models import TournamentRecord


class RecordTreeWidget(QTreeWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setColumnCount(2)
        self.setHeaderLabels(["Узел", "Значение"])
        self.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.header().setSectionResizeMode(1, QHeaderView.Stretch)

    def set_records(self, records: list[TournamentRecord]) -> None:
        self.clear()
        for index, record in enumerate(records, start=1):
            root = QTreeWidgetItem(
                [
                    f"Запись {index}",
                    f"{record.tournament_name} ({record.event_date.strftime('%d.%m.%Y')})",
                ]
            )
            self.addTopLevelItem(root)
            self._append_leaf(root, "Название турнира", record.tournament_name)
            self._append_leaf(root, "Дата проведения", record.event_date.strftime("%d.%m.%Y"))
            self._append_leaf(root, "Вид спорта", record.sport_name)
            self._append_leaf(root, "ФИО победителя", record.winner_full_name)
            self._append_leaf(root, "Размер призовых", f"{record.prize_amount:,.2f}".replace(",", " "))
            self._append_leaf(
                root,
                "Заработок победителя",
                f"{record.winner_earnings:,.2f}".replace(",", " "),
            )
            root.setExpanded(True)

    @staticmethod
    def _append_leaf(parent: QTreeWidgetItem, title: str, value: str) -> None:
        parent.addChild(QTreeWidgetItem([title, value]))
