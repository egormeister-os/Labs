from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.models import TournamentRecord, TournamentRecordInput
from app.repositories import TournamentRepository
from app.services import TournamentXmlWriter

SPORTS = [
    "Теннис",
    "Футбол",
    "Плавание",
    "Бокс",
    "Волейбол",
    "Биатлон",
    "Шахматы",
    "Легкая атлетика",
    "Хоккей",
    "Фигурное катание",
]

CITIES = [
    "Минск",
    "Брест",
    "Гродно",
    "Витебск",
    "Гомель",
    "Могилев",
    "Полоцк",
    "Пинск",
    "Барановичи",
    "Бобруйск",
]

LEVELS = ["Открытый", "Кубок", "Гран-при", "Мастерс", "Премьер-лига", "Суперсерия"]
FIRST_NAMES = [
    "Алексей",
    "Мария",
    "Игорь",
    "Ольга",
    "Дмитрий",
    "Елена",
    "Сергей",
    "Анна",
    "Павел",
    "Наталья",
    "Кирилл",
    "Дарья",
]
LAST_NAMES = [
    "Иванов",
    "Петров",
    "Сидоров",
    "Ковалев",
    "Громов",
    "Романенко",
    "Савченко",
    "Орлов",
    "Смирнов",
    "Богданов",
    "Соколов",
    "Жуков",
]
PATRONYMICS = [
    "Андреевич",
    "Игоревна",
    "Павлович",
    "Сергеевна",
    "Олегович",
    "Викторовна",
    "Денисович",
    "Михайловна",
    "Ильич",
    "Алексеевна",
]


def build_records(batch_index: int, count: int = 60) -> list[TournamentRecord]:
    records: list[TournamentRecord] = []
    base_date = date(2024 + batch_index - 1, 1 + batch_index, 6)

    for item_index in range(count):
        sport = SPORTS[(item_index + batch_index) % len(SPORTS)]
        city = CITIES[(item_index * 2 + batch_index) % len(CITIES)]
        level = LEVELS[(item_index + batch_index) % len(LEVELS)]
        season = 2024 + ((item_index + batch_index) % 3)
        tournament_name = f"{level} {city} по {sport} #{batch_index:02d}-{item_index + 1:02d}"

        first_name = FIRST_NAMES[(item_index + batch_index) % len(FIRST_NAMES)]
        last_name = LAST_NAMES[(item_index * 3 + batch_index) % len(LAST_NAMES)]
        patronymic = PATRONYMICS[(item_index * 5 + batch_index) % len(PATRONYMICS)]
        winner_name = f"{last_name} {first_name} {patronymic}"

        event_date = base_date + timedelta(days=item_index * 4 + batch_index)
        prize_amount = round(35_000 + batch_index * 7_500 + item_index * 1_875 + (season - 2024) * 950, 2)

        record = TournamentRecordInput(
            tournament_name=tournament_name,
            event_date=event_date,
            sport_name=sport,
            winner_full_name=winner_name,
            prize_amount=prize_amount,
        ).to_record()
        records.append(record)

    return records


def create_demo_files() -> None:
    data_dir = ROOT_DIR / "data"
    data_dir.mkdir(exist_ok=True)

    xml_writer = TournamentXmlWriter()
    all_records: list[TournamentRecord] = []

    for batch_index in range(1, 3):
        records = build_records(batch_index)
        all_records.extend(records)

        xml_writer.write(data_dir / f"demo_batch_{batch_index}.xml", records)
        batch_repository = TournamentRepository(data_dir / f"demo_batch_{batch_index}.db")
        try:
            batch_repository.replace_all(records)
        finally:
            batch_repository.close()

    main_repository = TournamentRepository(data_dir / "tournaments.db")
    try:
        main_repository.replace_all(all_records)
    finally:
        main_repository.close()


if __name__ == "__main__":
    create_demo_files()
