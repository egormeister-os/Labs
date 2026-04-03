from __future__ import annotations

from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtWidgets import (
    QAction,
    QActionGroup,
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QStackedWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from app.controllers import AppController
from app.models import ValidationError
from app.views.dialogs import DeleteDialog, RecordDialog, SearchDialog
from app.views.widgets import PaginationWidget, RecordTableWidget, RecordTreeWidget


class MainWindow(QMainWindow):
    def __init__(self, controller: AppController, parent=None) -> None:
        super().__init__(parent)
        self.controller = controller
        self.current_page = 1
        self.page_size = 10

        self.setWindowTitle("Каталог турниров")
        self.resize(1200, 750)

        self.page_title_label = QLabel("Текущий массив записей")
        self.page_title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.table_widget = RecordTableWidget()
        self.tree_widget = RecordTreeWidget()
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(self.table_widget)
        self.stacked_widget.addWidget(self.tree_widget)

        self.pagination_widget = PaginationWidget()
        self.pagination_widget.page_requested.connect(self.refresh_records)
        self.pagination_widget.page_size_changed.connect(self._change_page_size)

        central_widget = QWidget()
        central_layout = QVBoxLayout(central_widget)
        central_layout.addWidget(self.page_title_label)
        central_layout.addWidget(self.stacked_widget)
        central_layout.addWidget(self.pagination_widget)
        self.setCentralWidget(central_widget)

        self._create_actions()
        self._create_menu()
        self._create_toolbar()
        self.statusBar().showMessage(self._build_database_status_message())

        self.refresh_records(1)

    def _create_actions(self) -> None:
        self.open_database_action = QAction("Открыть БД...", self)
        self.save_database_as_action = QAction("Сохранить БД как...", self)
        self.import_xml_action = QAction("Импорт из XML...", self)
        self.export_xml_action = QAction("Экспорт в XML...", self)
        self.exit_action = QAction("Выход", self)
        self.add_record_action = QAction("Добавить запись", self)
        self.search_action = QAction("Поиск...", self)
        self.delete_action = QAction("Удаление...", self)
        self.refresh_action = QAction("Обновить", self)

        self.table_view_action = QAction("Таблица", self, checkable=True)
        self.tree_view_action = QAction("Дерево", self, checkable=True)
        self.table_view_action.setChecked(True)

        view_group = QActionGroup(self)
        view_group.addAction(self.table_view_action)
        view_group.addAction(self.tree_view_action)

        self.open_database_action.triggered.connect(self._open_database)
        self.save_database_as_action.triggered.connect(self._save_database_as)
        self.import_xml_action.triggered.connect(self._import_xml)
        self.export_xml_action.triggered.connect(self._export_xml)
        self.exit_action.triggered.connect(self.close)
        self.add_record_action.triggered.connect(self._open_add_dialog)
        self.search_action.triggered.connect(self._open_search_dialog)
        self.delete_action.triggered.connect(self._open_delete_dialog)
        self.refresh_action.triggered.connect(lambda: self.refresh_records(self.current_page))
        self.table_view_action.triggered.connect(lambda: self._set_view_mode(0))
        self.tree_view_action.triggered.connect(lambda: self._set_view_mode(1))

    def _create_menu(self) -> None:
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("Файл")
        file_menu.addAction(self.open_database_action)
        file_menu.addAction(self.save_database_as_action)
        file_menu.addSeparator()
        file_menu.addAction(self.import_xml_action)
        file_menu.addAction(self.export_xml_action)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)

        records_menu = menu_bar.addMenu("Записи")
        records_menu.addAction(self.add_record_action)
        records_menu.addAction(self.search_action)
        records_menu.addAction(self.delete_action)
        records_menu.addAction(self.refresh_action)

        view_menu = menu_bar.addMenu("Вид")
        view_menu.addAction(self.table_view_action)
        view_menu.addAction(self.tree_view_action)

    def _create_toolbar(self) -> None:
        toolbar = QToolBar("Основная панель", self)
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        for action in (
            self.open_database_action,
            self.save_database_as_action,
            self.import_xml_action,
            self.export_xml_action,
            self.add_record_action,
            self.search_action,
            self.delete_action,
            self.refresh_action,
            self.table_view_action,
            self.tree_view_action,
        ):
            toolbar.addAction(action)

    def refresh_records(self, page: int) -> None:
        page_result = self.controller.get_records_page(page, self.page_size)
        self.current_page = page_result.page
        self.table_widget.set_records(page_result.items)
        self.tree_widget.set_records(page_result.items)
        self.pagination_widget.update_state(
            current_page=page_result.page,
            page_size=page_result.page_size,
            current_page_count=page_result.current_page_count,
            total_count=page_result.total_count,
            total_pages=page_result.total_pages,
        )
        database_count = len(self.controller.opened_database_paths)
        self.page_title_label.setText(
            f"Объединенный массив записей. Показано {page_result.current_page_count} "
            f"из {page_result.total_count}. Открыто БД: {database_count}."
        )
        self.statusBar().showMessage(self._build_database_status_message())

    def _change_page_size(self, page_size: int) -> None:
        self.page_size = page_size
        self.current_page = 1
        self.refresh_records(self.current_page)

    def _set_view_mode(self, index: int) -> None:
        self.stacked_widget.setCurrentIndex(index)

    def _open_add_dialog(self) -> None:
        dialog = RecordDialog(self.controller.get_unique_sports(), self)
        if dialog.exec_():
            try:
                self.controller.add_record(dialog.record_input)
            except ValidationError as error:
                QMessageBox.warning(self, "Ошибка сохранения", str(error))
                return
            self.refresh_records(1)
            self.statusBar().showMessage("Запись добавлена.", 5000)

    def _open_search_dialog(self) -> None:
        dialog = SearchDialog(self.controller, self)
        dialog.exec_()

    def _open_delete_dialog(self) -> None:
        dialog = DeleteDialog(self.controller, self)
        if dialog.exec_():
            self.refresh_records(self.current_page)

    def _open_database(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Открыть базы данных",
            str(self.controller.current_database_path.parent),
            "SQLite (*.db *.sqlite3);;Все файлы (*)",
        )
        if not paths:
            return
        try:
            self.controller.open_databases(paths)
        except Exception as error:
            QMessageBox.warning(self, "Ошибка открытия БД", str(error))
            return
        self.refresh_records(1)

    def _save_database_as(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить базу данных как",
            str(self.controller.current_database_path),
            "SQLite (*.db *.sqlite3);;Все файлы (*)",
        )
        if not path:
            return
        target_path = self._ensure_suffix(Path(path), ".db")
        try:
            self.controller.save_database_as(target_path)
        except Exception as error:
            QMessageBox.warning(self, "Ошибка сохранения БД", str(error))
            return
        self.refresh_records(1)
        self.statusBar().showMessage(f"База данных сохранена: {target_path}", 5000)

    def _import_xml(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Импорт из XML",
            str(self.controller.current_database_path.parent),
            "XML (*.xml);;Все файлы (*)",
        )
        if not path:
            return

        answer = QMessageBox.question(
            self,
            "Подтверждение импорта",
            "Импорт из XML заменит текущий массив записей в базе данных. Продолжить?",
        )
        if answer != QMessageBox.Yes:
            return

        try:
            imported_count = self.controller.import_from_xml(path)
        except Exception as error:
            QMessageBox.warning(self, "Ошибка импорта", str(error))
            return

        self.refresh_records(1)
        self.statusBar().showMessage(f"Импортировано записей: {imported_count}.", 5000)

    def _export_xml(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Экспорт в XML",
            str(self.controller.current_database_path.parent / "tournaments.xml"),
            "XML (*.xml);;Все файлы (*)",
        )
        if not path:
            return
        target_path = self._ensure_suffix(Path(path), ".xml")
        try:
            exported_count = self.controller.export_to_xml(target_path)
        except Exception as error:
            QMessageBox.warning(self, "Ошибка экспорта", str(error))
            return
        self.statusBar().showMessage(f"Экспортировано записей: {exported_count}.", 5000)

    def closeEvent(self, event: QCloseEvent) -> None:
        self.controller.close()
        super().closeEvent(event)

    def _build_database_status_message(self) -> str:
        database_paths = self.controller.opened_database_paths
        if len(database_paths) == 1:
            return f"Текущая БД: {database_paths[0]}"

        names = ", ".join(path.name for path in database_paths)
        return (
            f"Открыто БД: {len(database_paths)}. "
            f"Основная: {database_paths[0].name}. "
            f"Подключены: {names}"
        )

    @staticmethod
    def _ensure_suffix(path: Path, suffix: str) -> Path:
        if path.suffix.lower() != suffix:
            return path.with_suffix(suffix)
        return path
