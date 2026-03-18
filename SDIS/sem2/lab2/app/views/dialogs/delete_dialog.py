from __future__ import annotations

from PyQt5.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from app.controllers import AppController
from app.models import ValidationError
from app.views.dialogs.criteria_form import CriteriaFormWidget


class DeleteDialog(QDialog):
    def __init__(self, controller: AppController, parent=None) -> None:
        super().__init__(parent)
        self.controller = controller
        self.deleted_count = 0
        self.setWindowTitle("Удаление записей")
        self.resize(700, 420)

        self.criteria_form = CriteriaFormWidget(self.controller.get_unique_sports())
        self.delete_button = QPushButton("Удалить")
        self.reset_button = QPushButton("Сбросить")
        self.button_box = QDialogButtonBox(QDialogButtonBox.Cancel)

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.delete_button)
        buttons_layout.addWidget(self.reset_button)
        buttons_layout.addStretch(1)
        buttons_layout.addWidget(self.button_box)

        layout = QVBoxLayout(self)
        layout.addWidget(self.criteria_form)
        layout.addLayout(buttons_layout)

        self.delete_button.clicked.connect(self._delete_records)
        self.reset_button.clicked.connect(self.criteria_form.reset)
        self.button_box.rejected.connect(self.reject)

    def showEvent(self, event) -> None:
        self.criteria_form.refresh_sports(self.controller.get_unique_sports())
        super().showEvent(event)

    def _delete_records(self) -> None:
        try:
            criteria = self.criteria_form.to_criteria()
            if criteria.is_empty():
                QMessageBox.warning(
                    self,
                    "Недостаточно условий",
                    "Для удаления необходимо задать хотя бы одно условие.",
                )
                return

            self.deleted_count = self.controller.delete_records(criteria)
        except ValidationError as error:
            QMessageBox.warning(self, "Ошибка условий удаления", str(error))
            return

        if self.deleted_count == 0:
            QMessageBox.information(
                self,
                "Результат удаления",
                "Записи по указанным условиям не найдены.",
            )
        else:
            QMessageBox.information(
                self,
                "Результат удаления",
                f"Удалено записей: {self.deleted_count}.",
            )
        self.accept()
