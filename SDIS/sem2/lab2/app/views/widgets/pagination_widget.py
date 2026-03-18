from __future__ import annotations

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QWidget,
)


class PaginationWidget(QWidget):
    page_requested = pyqtSignal(int)
    page_size_changed = pyqtSignal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._current_page = 1
        self._total_pages = 1

        self.first_button = QPushButton("<<")
        self.previous_button = QPushButton("<")
        self.next_button = QPushButton(">")
        self.last_button = QPushButton(">>")
        self.page_size_combo = QComboBox()
        self.page_size_combo.addItems(["5", "10", "20", "50"])
        self.page_size_combo.setCurrentText("10")

        self.info_label = QLabel()
        self.info_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(QLabel("На странице:"))
        layout.addWidget(self.page_size_combo)
        layout.addSpacing(12)
        layout.addWidget(self.first_button)
        layout.addWidget(self.previous_button)
        layout.addWidget(self.next_button)
        layout.addWidget(self.last_button)
        layout.addSpacing(12)
        layout.addWidget(self.info_label)

        self.first_button.clicked.connect(lambda: self.page_requested.emit(1))
        self.previous_button.clicked.connect(self._go_previous)
        self.next_button.clicked.connect(self._go_next)
        self.last_button.clicked.connect(lambda: self.page_requested.emit(self._total_pages))
        self.page_size_combo.currentTextChanged.connect(self._emit_page_size_changed)

        self.update_state(
            current_page=1,
            page_size=int(self.page_size_combo.currentText()),
            current_page_count=0,
            total_count=0,
            total_pages=1,
        )

    def update_state(
        self,
        current_page: int,
        page_size: int,
        current_page_count: int,
        total_count: int,
        total_pages: int,
    ) -> None:
        self._current_page = current_page
        self._total_pages = max(1, total_pages)

        index = self.page_size_combo.findText(str(page_size))
        if index >= 0:
            self.page_size_combo.blockSignals(True)
            self.page_size_combo.setCurrentIndex(index)
            self.page_size_combo.blockSignals(False)

        self.info_label.setText(
            (
                f"Записей на странице: {current_page_count}. "
                f"Всего записей: {total_count}. "
                f"Страница {self._current_page} из {self._total_pages}."
            )
        )

        has_previous = total_count > 0 and self._current_page > 1
        has_next = total_count > 0 and self._current_page < self._total_pages
        self.first_button.setEnabled(has_previous)
        self.previous_button.setEnabled(has_previous)
        self.next_button.setEnabled(has_next)
        self.last_button.setEnabled(has_next)

    def _go_previous(self) -> None:
        self.page_requested.emit(max(1, self._current_page - 1))

    def _go_next(self) -> None:
        self.page_requested.emit(min(self._total_pages, self._current_page + 1))

    def _emit_page_size_changed(self, value: str) -> None:
        self.page_size_changed.emit(int(value))
