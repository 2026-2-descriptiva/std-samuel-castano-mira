from pathlib import Path

import pandas as pd

DATA = Path(__file__).resolve().parents[1] / "data"


def leer(nombre):
    """Lee data/<nombre>.tsv como DataFrame."""
    return pd.read_csv(DATA / f"{nombre}.tsv", sep="\t")
