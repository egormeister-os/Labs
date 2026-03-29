from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


class Config:
    SECRET_KEY = "lab4-police-system-dev"
    DATA_DIR = BASE_DIR / "pickle_storage"
