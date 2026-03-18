from __future__ import annotations

from datetime import date
from pathlib import Path
from xml.dom.minidom import Document
import xml.sax

from app.models import TournamentRecord, TournamentRecordInput


class TournamentXmlWriter:
    def write(self, target_path: str | Path, records: list[TournamentRecord]) -> None:
        path = Path(target_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        document = Document()
        root = document.createElement("tournaments")
        root.setAttribute("count", str(len(records)))
        document.appendChild(root)

        for record in records:
            tournament_element = document.createElement("tournament")
            if record.id is not None:
                tournament_element.setAttribute("id", str(record.id))
            root.appendChild(tournament_element)

            self._append_text_element(document, tournament_element, "tournament_name", record.tournament_name)
            self._append_text_element(document, tournament_element, "event_date", record.event_date.isoformat())
            self._append_text_element(document, tournament_element, "sport_name", record.sport_name)
            self._append_text_element(document, tournament_element, "winner_full_name", record.winner_full_name)
            self._append_text_element(document, tournament_element, "prize_amount", f"{record.prize_amount:.2f}")
            self._append_text_element(
                document,
                tournament_element,
                "winner_earnings",
                f"{record.winner_earnings:.2f}",
            )

        with path.open("wb") as xml_file:
            xml_file.write(document.toprettyxml(indent="  ", encoding="utf-8"))

    @staticmethod
    def _append_text_element(
        document: Document,
        parent,
        tag_name: str,
        value: str,
    ) -> None:
        element = document.createElement(tag_name)
        element.appendChild(document.createTextNode(value))
        parent.appendChild(element)


class TournamentXmlReader:
    def read(self, source_path: str | Path) -> list[TournamentRecord]:
        handler = _TournamentHandler()
        xml.sax.parse(str(source_path), handler)
        return handler.records


class _TournamentHandler(xml.sax.ContentHandler):
    TRACKED_FIELDS = {
        "tournament_name",
        "event_date",
        "sport_name",
        "winner_full_name",
        "prize_amount",
        "winner_earnings",
    }

    def __init__(self) -> None:
        super().__init__()
        self.records: list[TournamentRecord] = []
        self._current_field: str | None = None
        self._buffer: list[str] = []
        self._current_data: dict[str, str] = {}

    def startElement(self, name: str, attrs) -> None:
        if name == "tournament":
            self._current_data = {}
            return
        if name in self.TRACKED_FIELDS:
            self._current_field = name
            self._buffer = []

    def characters(self, content: str) -> None:
        if self._current_field is not None:
            self._buffer.append(content)

    def endElement(self, name: str) -> None:
        if name in self.TRACKED_FIELDS and self._current_field == name:
            self._current_data[name] = "".join(self._buffer).strip()
            self._current_field = None
            self._buffer = []
            return

        if name == "tournament":
            record_input = TournamentRecordInput(
                tournament_name=self._current_data["tournament_name"],
                event_date=date.fromisoformat(self._current_data["event_date"]),
                sport_name=self._current_data["sport_name"],
                winner_full_name=self._current_data["winner_full_name"],
                prize_amount=float(self._current_data["prize_amount"]),
            )
            self.records.append(record_input.to_record())
