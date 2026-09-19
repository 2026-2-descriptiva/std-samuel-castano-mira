"""
Diagnostico de calidad del archivo de ventas.

Sirve para ver que hay que limpiar (antes) y para comprobar que quedo limpio
(despues). No modifica datos: solo describe.
"""

import os

import pandas as pd

from .clean import INPUT_FILE, OUTPUT_FILE, collapse_spaces, group_key, split_legal_suffix


def column_report(dataframe):
    """Resumen por columna: tipo, nulos y cantidad de valores distintos."""

    return pd.DataFrame(
        {
            "dtype": dataframe.dtypes.astype(str),
            "nulls": dataframe.isna().sum(),
            "unique": dataframe.nunique(dropna=True),
        }
    )


def text_variants(series):
    """
    Agrupa las variantes de escritura de una columna de texto.

    Retorna solo los grupos con mas de una forma escrita, que son los que
    delatan un problema de consistencia.
    """

    groups = {}
    for value in series.dropna().unique():
        tokens, suffix = split_legal_suffix(value)
        groups.setdefault(group_key(tokens, suffix), set()).add(collapse_spaces(value))
    return {key: sorted(values) for key, values in groups.items() if len(values) > 1}


def outliers_iqr(series, factor=1.5):
    """Valores fuera del rango intercuartilico, que suelen ser errores de digitacion."""

    numbers = pd.to_numeric(series, errors="coerce").dropna()
    q1, q3 = numbers.quantile(0.25), numbers.quantile(0.75)
    span = factor * (q3 - q1)
    return numbers[(numbers < q1 - span) | (numbers > q3 + span)]


def report(input_file=INPUT_FILE, output_file=OUTPUT_FILE):
    """Imprime el diagnostico del archivo crudo y, si existe, del limpio."""

    raw = pd.read_csv(input_file, encoding="utf-8-sig", dtype=str)
    print("=== ANTES ===")
    print(column_report(raw).to_string())
    print("\nfilas duplicadas:", raw.duplicated().sum())
    for column in ["supplier", "COUNTRY", "City "]:
        variants = text_variants(raw[column])
        print(f"\nvariantes de escritura en '{column.strip()}': {len(variants)} grupos")
        for values in list(variants.values())[:5]:
            print("   ", values)

    if not os.path.exists(output_file):
        return

    clean = pd.read_csv(output_file)
    print("\n=== DESPUES ===")
    print(column_report(clean).to_string())
    print("\nfilas duplicadas:", clean.duplicated().sum())
    for column in ["amount", "unit_price", "weight"]:
        found = outliers_iqr(clean[column])
        print(f"outliers en '{column}': {len(found)} -> {found.tolist()}")


if __name__ == "__main__":
    report()
