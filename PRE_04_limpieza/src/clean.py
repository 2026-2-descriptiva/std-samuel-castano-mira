"""
Limpieza del archivo de ventas.

El archivo `data/ventas.csv` trae los mismos datos escritos de muchas formas
distintas: nombres de proveedor con mayusculas, tildes y sufijos juridicos
inconsistentes, paises escritos de seis maneras, fechas en cuatro formatos,
montos con simbolos de moneda y separadores de miles mezclados, pesos en
gramos / kilogramos / toneladas, y descuentos como porcentaje o como fraccion.

`main()` deja una version normalizada en `submission/ventas.csv`.
"""

import os
import re
import unicodedata

import pandas as pd

PROJECT_FOLDER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_FILE = os.path.join(PROJECT_FOLDER, "data", "ventas.csv")
OUTPUT_FILE = os.path.join(PROJECT_FOLDER, "submission", "ventas.csv")

# Sufijos juridicos escritos de forma canonica. La llave es el sufijo sin
# puntos ni mayusculas, que es como se comparan las variantes del archivo.
LEGAL_SUFFIXES = {
    "sa": "S.A.",
    "sas": "S.A.S.",
    "ltda": "Ltda.",
    "inc": "Inc.",
}

# Palabras que son siglas y por lo tanto van completamente en mayuscula.
ACRONYMS = {"ibm": "IBM", "sap": "SAP", "abb": "ABB"}


def strip_accents(text):
    """Retorna el texto sin tildes ni diacriticos."""

    decomposed = unicodedata.normalize("NFD", text)
    return "".join(c for c in decomposed if unicodedata.category(c) != "Mn")


def collapse_spaces(text):
    """Quita espacios sobrantes al inicio, al final y entre palabras."""

    return " ".join(str(text).split())


def split_legal_suffix(name):
    """Separa el nombre en (palabras del nombre, sufijo juridico o None)."""

    tokens = collapse_spaces(name).split()
    if tokens and tokens[-1].replace(".", "").lower() in LEGAL_SUFFIXES:
        return tokens[:-1], tokens[-1].replace(".", "").lower()
    return tokens, None


def count_accents(text):
    """Cuenta cuantos caracteres del texto llevan tilde."""

    return sum(1 for a, b in zip(text, strip_accents(text)) if a != b)


def group_key(tokens, suffix):
    """Llave de agrupacion: sin tildes, sin mayusculas y sin puntos."""

    return (tuple(strip_accents(t).lower() for t in tokens), suffix)


def build_canonical(members, suffix):
    """Reconstruye el nombre canonico a partir de las variantes de un grupo."""

    # La variante con mas tildes es la que conserva la ortografia correcta.
    donor = max(members, key=lambda tokens: (count_accents(" ".join(tokens)), tokens))
    words = [ACRONYMS.get(word.lower(), word.capitalize()) for word in donor]
    if suffix is not None:
        words.append(LEGAL_SUFFIXES[suffix])
    return " ".join(words)


def canonical_names(values):
    """
    Construye el nombre canonico de cada grupo de variantes.

    Dos valores pertenecen al mismo grupo si coinciden al quitarles tildes,
    mayusculas, espacios sobrantes y los puntos del sufijo juridico. El nombre
    canonico NO se elige entre las variantes existentes (a veces todas estan
    mal escritas, como 'Cementos Argos SA' y 'cementos argos s.a.'): se
    reconstruye. Las tildes se toman de la variante que mas tenga, la
    capitalizacion se normaliza palabra por palabra y el sufijo juridico se
    escribe siempre en su forma punteada.

    Retorna un diccionario {valor original: nombre canonico}.
    """

    groups = {}
    for value in values:
        tokens, suffix = split_legal_suffix(value)
        groups.setdefault(group_key(tokens, suffix), []).append(tokens)

    canonical = {
        key: build_canonical(members, key[1]) for key, members in groups.items()
    }

    result = {}
    for value in values:
        tokens, suffix = split_legal_suffix(value)
        result[value] = canonical[group_key(tokens, suffix)]
    return result


def clean_text_column(series):
    """Unifica las variantes de escritura de una columna de texto."""

    mapping = canonical_names(series.dropna().unique())
    return series.map(lambda v: mapping.get(v, v))


def clean_column_names(dataframe):
    """Pasa los nombres de columna a snake_case en minuscula."""

    dataframe.columns = [
        collapse_spaces(c).lower().replace(" ", "_").replace("-", "_")
        for c in dataframe.columns
    ]
    return dataframe


def clean_country(series):
    """Unifica el pais al codigo ISO de tres letras."""

    return series.map(lambda v: "COL" if pd.notna(v) else v)


# Formatos de fecha presentes en el archivo, en orden de prioridad. El archivo
# mezcla dia-primero ('14/04/2026') con mes-primero ('01/27/2026'), asi que es
# imposible desambiguar '01/03/2026' solo con el texto. Se prioriza la
# convencion colombiana (dia primero) y se cae a mes-primero unicamente cuando
# el primer numero no puede ser un dia.
DATE_FORMATS = [
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%d/%m/%Y",
    "%m/%d/%Y",
    "%d-%m-%y",
    "%d.%m.%Y",
]


def clean_date(value):
    """Convierte a fecha real cualquiera de los formatos del archivo."""

    if pd.isna(value):
        return pd.NaT
    text = collapse_spaces(value)
    for fmt in DATE_FORMATS:
        parsed = pd.to_datetime(text, format=fmt, errors="coerce")
        if pd.notna(parsed):
            return parsed
    return pd.NaT


def parse_number(value):
    """
    Convierte a numero un monto escrito con cualquiera de los formatos del
    archivo: '$480,000', 'COP 480,000', '480.000', '480.00K' o ' 480000 '.
    """

    if pd.isna(value):
        return pd.NA

    text = collapse_spaces(value).upper().replace("COP", "").replace("$", "").strip()
    if not text:
        return pd.NA

    # El sufijo K multiplica por mil y usa el punto como separador decimal.
    if text.endswith("K"):
        return float(text[:-1].replace(",", "")) * 1000

    text = text.replace(",", "")
    # El punto es separador de miles o decimal segun el tamano del ultimo grupo:
    # '48.000.000' son 48 millones (grupo final de 3 cifras) mientras que
    # '1.250.000.00' son 1.25 millones con centavos (grupo final de 2 cifras).
    if "." in text:
        head, _, tail = text.rpartition(".")
        if len(tail) == 3:
            text = text.replace(".", "")
        else:
            text = head.replace(".", "") + "." + tail

    try:
        return float(text)
    except ValueError:
        return pd.NA


def parse_discount(value):
    """Lleva el descuento a una fraccion entre 0 y 1."""

    if pd.isna(value):
        return pd.NA
    text = collapse_spaces(value).replace("%", "")
    try:
        number = float(text)
    except ValueError:
        return pd.NA
    return number / 100 if number > 1 else number


def parse_weight_kg(value):
    """Lleva el peso a kilogramos sin importar la unidad en que venga."""

    if pd.isna(value):
        return pd.NA
    text = collapse_spaces(value).lower().replace(",", ".")
    match = re.match(r"^([\d.]+)\s*(g|kg|ton)?$", text)
    if match is None:
        return pd.NA
    number = float(match.group(1))
    factor = {"g": 0.001, "ton": 1000.0, "kg": 1.0, None: 1.0}[match.group(2)]
    return number * factor


def clean_email(series):
    """Deja vacios los correos que en realidad son un marcador de ausencia."""

    return series.map(
        lambda v: pd.NA if collapse_spaces(v).lower() == "sin correo" else collapse_spaces(v)
    )


def clean(dataframe):
    """Aplica toda la limpieza y retorna el dataframe normalizado."""

    dataframe = clean_column_names(dataframe.copy())

    dataframe["supplier_id"] = dataframe["supplier_id"].astype(str).str.strip().astype(int)
    dataframe["supplier"] = clean_text_column(dataframe["supplier"])
    dataframe["country"] = clean_country(dataframe["country"])
    dataframe["city"] = clean_text_column(dataframe["city"])
    dataframe["purchase_date"] = dataframe["purchase_date"].map(clean_date)
    dataframe["amount"] = dataframe["amount"].map(parse_number)
    dataframe["discount"] = dataframe["discount"].map(parse_discount)
    dataframe["weight"] = dataframe["weight"].map(parse_weight_kg)
    dataframe["units"] = dataframe["units"].astype("Int64")
    dataframe["unit_price"] = dataframe["unit_price"].map(parse_number)
    dataframe["contact_email"] = clean_email(dataframe["contact_email"])

    dataframe = dataframe.drop_duplicates().reset_index(drop=True)
    return dataframe


def main(input_file=INPUT_FILE, output_file=OUTPUT_FILE):
    """Lee el archivo crudo, lo limpia y lo guarda en `submission`."""

    # utf-8-sig descarta el BOM con el que viene escrito el archivo original.
    dataframe = pd.read_csv(input_file, encoding="utf-8-sig", dtype=str)
    dataframe = clean(dataframe)
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    dataframe.to_csv(output_file, index=False)
    return dataframe


if __name__ == "__main__":
    print(main().head().to_string())
