import gzip
from pathlib import Path

RUTA = Path(__file__).resolve().parents[1] / "data" / "data.csv.gz"


def leer_filas():
    """Lee data.csv.gz y retorna lista de listas (5 columnas de texto)."""
    with gzip.open(RUTA, "rt", encoding="utf-8") as f:
        return [linea.rstrip("\n").split("\t") for linea in f if linea.strip()]


def pares(texto):
    """Convierte 'clave:valor,...' en lista de (clave, int(valor))."""
    return [(p.split(":")[0], int(p.split(":")[1])) for p in texto.split(",")]
