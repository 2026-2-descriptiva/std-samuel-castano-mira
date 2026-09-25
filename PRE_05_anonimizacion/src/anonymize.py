"""
Anonimizacion del archivo de clientes.

`data/raw.csv` trae identificadores directos (nombre, cedula, correo, numero de
tarjeta) y cuasi-identificadores (edad, ciudad, ocupacion). Los directos se
eliminan, pero eso no basta: 556 de los 600 registros son unicos por la
combinacion (edad, ciudad, ocupacion), asi que cualquiera con una lista de
nombres y esos tres datos -- exactamente lo que contiene `data/auxiliary.csv` --
puede volver a identificar a casi todo el mundo.

Por eso los cuasi-identificadores se generalizan (edad a rangos, ciudad a
region, ocupacion a sector) y se suprimen los grupos que aun asi queden con
menos de `k` personas. El resultado cumple k-anonimato: cada registro es
indistinguible de al menos otros k-1.
"""

import os

import pandas as pd

PROJECT_FOLDER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_FILE = os.path.join(PROJECT_FOLDER, "data", "raw.csv")
AUXILIARY_FILE = os.path.join(PROJECT_FOLDER, "data", "auxiliary.csv")
OUTPUT_FILE = os.path.join(PROJECT_FOLDER, "submission", "anonymized.csv")

# Identificadores directos: senalan a una persona sin ayuda de nada mas.
DIRECT_IDENTIFIERS = ["name", "document_id", "email", "loyalty_card_number"]

# Cuasi-identificadores: por si solos no identifican, pero combinados si.
QUASI_IDENTIFIERS = ["age_range", "region", "sector"]

REGIONS = {
    "Medellín": "Antioquia",
    "Itagüí": "Antioquia",
    "Bello": "Antioquia",
    "Envigado": "Antioquia",
    "Rionegro": "Antioquia",
    "Bogotá": "Bogotá D.C.",
    "Cali": "Valle del Cauca",
    "Cartagena": "Caribe",
    "Barranquilla": "Caribe",
    "Pereira": "Eje Cafetero",
    "Manizales": "Eje Cafetero",
    "Bucaramanga": "Santander",
}

SECTORS = {
    "Enfermera": "Salud",
    "Médico": "Salud",
    "Docente": "Educación",
    "Ingeniero de sistemas": "Tecnología",
    "Técnico electricista": "Tecnología",
    "Contadora": "Administración y finanzas",
    "Analista financiera": "Administración y finanzas",
    "Administradora": "Administración y finanzas",
    "Arquitecta": "Diseño y construcción",
    "Diseñadora gráfica": "Diseño y construcción",
    "Comerciante": "Comercio",
    "Abogada": "Legal",
}

# Rangos de edad anchos a proposito: con bandas de 10 anos el k-anonimato de 5
# obliga a suprimir el 44% de los registros; con estas tres bandas la perdida
# baja al 26% sin ceder privacidad (ver comparacion en el notebook).
AGE_BINS = [0, 34, 49, 200]
AGE_LABELS = ["20-34", "35-49", "50+"]

SPEND_BINS = [0, 2_000_000, 4_000_000, 6_000_000, 8_000_000, float("inf")]
SPEND_LABELS = ["0-2M", "2-4M", "4-6M", "6-8M", "8M+"]


def drop_direct_identifiers(dataframe):
    """Elimina las columnas que identifican a una persona por si solas."""

    return dataframe.drop(columns=DIRECT_IDENTIFIERS)


def generalize(dataframe):
    """Reemplaza los cuasi-identificadores por versiones menos precisas."""

    dataframe = dataframe.copy()
    dataframe["age_range"] = pd.cut(
        dataframe["age"], bins=AGE_BINS, labels=AGE_LABELS, right=True
    )
    dataframe["region"] = dataframe["city"].map(REGIONS)
    dataframe["sector"] = dataframe["occupation"].map(SECTORS)
    dataframe["spend_range"] = pd.cut(
        dataframe["annual_spend"], bins=SPEND_BINS, labels=SPEND_LABELS, right=True
    )
    return dataframe[QUASI_IDENTIFIERS + ["spend_range"]]


def suppress_small_groups(dataframe, k):
    """Descarta los registros cuyo grupo de cuasi-identificadores tiene menos de k."""

    sizes = dataframe.groupby(QUASI_IDENTIFIERS, observed=True)[
        QUASI_IDENTIFIERS[0]
    ].transform("size")
    return dataframe[sizes >= k].reset_index(drop=True)


def k_anonymity(dataframe):
    """Tamano del grupo mas pequeno: el k que realmente cumple la tabla."""

    if dataframe.empty:
        return 0
    return int(dataframe.groupby(QUASI_IDENTIFIERS, observed=True).size().min())


def reidentification_risk(anonymized, auxiliary_file=AUXILIARY_FILE):
    """
    Cuenta cuantas personas de la lista del atacante quedarian identificadas.

    `auxiliary.csv` es justamente lo que un atacante podria conseguir por fuera:
    nombre + edad + ciudad + ocupacion. Se generaliza igual que la tabla
    publicada y se mira a cuantos registros corresponde cada persona.
    """

    auxiliary = pd.read_csv(auxiliary_file)
    auxiliary = auxiliary.assign(annual_spend=0)
    auxiliary = generalize(auxiliary)

    sizes = anonymized.groupby(QUASI_IDENTIFIERS, observed=True).size()
    matches = [
        sizes.get((row.age_range, row.region, row.sector), 0)
        for row in auxiliary.itertuples()
    ]
    return {
        "personas": len(matches),
        "identificadas": sum(1 for m in matches if m == 1),
        "sin_coincidencia": sum(1 for m in matches if m == 0),
        "minimo_candidatos": min(m for m in matches if m > 0) if any(matches) else 0,
    }


def anonymize(input_file=INPUT_FILE, k=5):
    """Aplica el proceso completo y retorna la tabla anonimizada."""

    dataframe = pd.read_csv(input_file)
    dataframe = drop_direct_identifiers(dataframe)
    dataframe = generalize(dataframe)
    return suppress_small_groups(dataframe, k)


def main(input_file=INPUT_FILE, output_file=OUTPUT_FILE, k=5):
    """Anonimiza el archivo y lo guarda en `submission`."""

    original = pd.read_csv(input_file)
    anonymized = anonymize(input_file, k)

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    anonymized.to_csv(output_file, index=False)

    print(f"registros: {len(original)} -> {len(anonymized)} "
          f"({len(anonymized) / len(original):.1%} conservado)")
    print(f"k-anonimato alcanzado: {k_anonymity(anonymized)} (objetivo {k})")
    print("riesgo de re-identificacion:", reidentification_risk(anonymized))
    return anonymized


if __name__ == "__main__":
    main()
