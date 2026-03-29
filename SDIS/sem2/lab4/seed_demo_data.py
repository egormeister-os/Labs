from app.services import PoliceSystem
from app.storage import PickleStorage


def seed_demo_data() -> None:
    storage = PickleStorage()
    system = PoliceSystem(storage=storage)

    system.police = system.storage.load()["police"].__class__()
    system.applications = []
    system.history = []
    system.citizens = []
    system.security = system.storage.load()["security"].__class__()
    system.laws = []

    for article, severity, desc in [
        (101, 1, "Minor offense"),
        (201, 3, "Theft"),
        (301, 5, "Violent crime"),
        (404, 4, "Fraud"),
        (505, 2, "Property damage"),
    ]:
        system.add_law(article, severity, desc)

    for zone in ["Downtown", "Riverside", "OldTown"]:
        system.add_zone(zone)

    for name, zone in [
        ("John Smith", "Downtown"),
        ("Alice Brown", "Downtown"),
        ("Mark Taylor", "Riverside"),
        ("Emily Davis", "OldTown"),
        ("Victor Stone", "OldTown"),
    ]:
        system.add_citizen(name, zone=zone)

    for lastname, zone in [
        ("Miller", "Downtown"),
        ("Moore", "Downtown"),
        ("Clark", "Riverside"),
        ("Adams", "OldTown"),
    ]:
        system.hire_policeman(lastname, zone)

    system.list_policemen()[0]._fatigue = 2
    system.list_policemen()[3]._fatigue = 6
    system.list_policemen()[3].check_exhaustion()

    system.create_statement("Bike theft near station", "Downtown", 0, 1)
    system.create_statement("Shop vandalism", "Riverside", 2, 4)
    system.create_statement("Street assault", "OldTown", 4, 2)

    system.history.append("Demo data prepared for manual presentation")
    system.save_data()


if __name__ == "__main__":
    seed_demo_data()
