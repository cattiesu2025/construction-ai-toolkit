import os
from pathlib import Path
import pandas as pd

_DATA_DIR = Path(__file__).parents[4] / "data"


def _load(filename: str) -> pd.DataFrame:
    path = _DATA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {path}")
    return pd.read_csv(path)


def projects() -> pd.DataFrame:
    return _load("projects.csv")


def tasks() -> pd.DataFrame:
    return _load("tasks.csv")


def defects() -> pd.DataFrame:
    return _load("defects.csv")


def compliance() -> pd.DataFrame:
    return _load("compliance.csv")


def historical_delays() -> pd.DataFrame:
    return _load("historical_delays.csv")
