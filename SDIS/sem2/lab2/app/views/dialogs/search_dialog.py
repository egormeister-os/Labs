from __future__ import annotations

from PyQt5.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from app.controllers import AppController
from app.models import SearchCriteria, ValidationError
from app.views.dialogs.criteria_form import CriteriaFormWidget
from app.views.widgets import PaginationWidget, RecordTableWidget


class SearchDialog(QDialog):
    def __init__(self, controller: AppController, parent=None) -> None:
        super().__init__(parent)
        self.controller = controller
        self.setWindowTitle("Поиск записей")
        self.resize(1000, 700)

        self.current_page = 1
        self.page_size = 10
        self.current_criteria = SearchCriteria()

        self.criteria_form = CriteriaFormWidget(self.controller.get_unique_sports())
        self.summary_label = QLabel()
        self.results_table = RecordTableWidget()
        self.pagination_widget = PaginationWidget()

        self.search_button = QPushButton("Найти")
        self.reset_button = QPushButton("Сбросить")
        close_box = QDialogButtonBox(QDialogButtonBox.Close)
        close_box.rejected.connect(self.reject)

        button_row = QHBoxLayout()
        button_row.addWidget(self.search_button)
        button_row.addWidget(self.reset_button)
        button_row.addStretch(1)
        button_row.addWidget(close_box)

        layout = QVBoxLayout(self)
        layout.addWidget(self.criteria_form)
        layout.addLayout(button_row)
        layout.addWidget(self.summary_label)
        layout.addWidget(self.results_table)
        layout.addWidget(self.pagination_widget)

        self.search_button.clicked.connect(self._run_search_from_form)
        self.reset_button.clicked.connect(self._reset_form)
        self.pagination_widget.page_requested.connect(self._load_page)
        self.pagination_widget.page_size_changed.connect(self._change_page_size)

        self._run_search_from_form()

    def showEvent(self, event) -> None:
        self.criteria_form.refresh_sports(self.controller.get_unique_sports())
        super().showEvent(event)

    def _run_search_from_form(self) -> None:
        try:
            self.current_criteria = self.criteria_form.to_criteria()
        except ValidationError as error:
            QMessageBox.warning(self, "Ошибка условий поиска", str(error))
            return

        self.current_page = 1
        self._load_page(self.current_page)

    def _load_page(self, page: int) -> None:
        page_result = self.controller.search_records(self.current_criteria, page, self.page_size)
        self.current_page = page_result.page
        self.results_table.set_records(page_result.items)
        self.pagination_widget.update_state(
            current_page=page_result.page,
            page_size=page_result.page_size,
            current_page_count=page_result.current_page_count,
            total_count=page_result.total_count,
            total_pages=page_result.total_pages,
        )
        self.summary_label.setText(
            f"Найдено уникальных записей: {page_result.total_count}. "
            f"На текущей странице показано: {page_result.current_page_count}."
        )

    def _change_page_size(self, page_size: int) -> None:
        self.page_size = page_size
        self.current_page = 1
        self._load_page(self.current_page)

    def _reset_form(self) -> None:
        self.criteria_form.reset()
        self.current_criteria = SearchCriteria()
        self.current_page = 1
        self._load_page(self.current_page)
