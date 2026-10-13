def main():
    """
    Antes de limpiar o analizar un conjunto de datos, un analista debe
    documentar qué problemas tiene. En este laboratorio usted no va a limpiar
    `data/ventas.csv.gz`: va a construir un reporte de calidad que deje evidencia
    de sus problemas, tal como están en el archivo.

    Lea `data/ventas.csv.gz` sin modificar sus valores. Para trabajar con los
    encabezados, normalícelos: páselos a minúsculas, elimine los espacios al
    inicio y al final (y cualquier marca BOM) y reemplace los espacios
    internos por `_`. Las columnas requeridas son `supplier_id`, `supplier`,
    `country`, `city`, `purchase_date`, `amount`, `discount`, `weight`,
    `units`, `unit_price` y `contact_email`.

    Escriba el reporte en `submission/data_quality_report.json` con estas
    claves:

    - `row_count`: cantidad de filas de datos.
    - `column_count`: cantidad de columnas.
    - `missing_required_columns`: lista ordenada de columnas requeridas que no
      están en el archivo.
    - `unexpected_columns`: lista ordenada de columnas del archivo que no son
      requeridas.
    - `duplicate_row_count`: cantidad de filas idénticas a una fila anterior.
    - `duplicate_supplier_id_row_count`: cantidad de filas cuyo `supplier_id`
      aparece más de una vez (cuente todas esas filas, no solo las
      repetidas).
    - `missing_value_count_by_column`: diccionario con la cantidad de valores
      faltantes de cada columna. Considere faltantes las celdas vacías y las
      que contienen `N/A`.
    - `invalid_email_count`: cantidad de valores de `contact_email` que no
      tienen la forma `usuario@dominio.extension`.
    - `invalid_unit_count`: cantidad de valores numéricos de `units` que no son
      enteros positivos. Los valores faltantes no se cuentan aquí.
    - `country_values`: lista ordenada de los valores distintos de `country`,
      escritos exactamente como aparecen en el archivo.

    La función también debe retornar el reporte como un diccionario.

    Ejemplo del formato del reporte:

        {
          "row_count": 103,
          "column_count": 11,
          "missing_required_columns": [],
          ...
          "country_values": [" Colombia ", "CO", ...]
        }
    """

    import json
    import re
    from pathlib import Path

    import pandas as pd

    base = Path(__file__).resolve().parents[1]
    requeridas = [
        "supplier_id", "supplier", "country", "city", "purchase_date",
        "amount", "discount", "weight", "units", "unit_price", "contact_email",
    ]

    # Todo como texto, sin convertir faltantes ni limpiar valores.
    df = pd.read_csv(
        base / "data" / "ventas.csv.gz",
        dtype=str,
        keep_default_na=False,
        encoding="utf-8-sig",
    )
    df.columns = [
        c.replace("\ufeff", "").strip().lower().replace(" ", "_") for c in df.columns
    ]

    faltante = df.apply(lambda s: s.str.strip().isin(["", "N/A"]))

    def unidad_invalida(valor):
        try:
            n = float(valor)
        except ValueError:
            return False
        return not (n > 0 and n == int(n))

    unidades = df["units"][~faltante["units"]] if "units" in df else []
    correos = df["contact_email"] if "contact_email" in df else []
    patron = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s.]+$")

    reporte = {
        "row_count": int(len(df)),
        "column_count": int(len(df.columns)),
        "missing_required_columns": sorted(set(requeridas) - set(df.columns)),
        "unexpected_columns": sorted(set(df.columns) - set(requeridas)),
        "duplicate_row_count": int(df.duplicated().sum()),
        "duplicate_supplier_id_row_count": (
            int(df["supplier_id"].duplicated(keep=False).sum())
            if "supplier_id" in df
            else 0
        ),
        "missing_value_count_by_column": {
            c: int(faltante[c].sum()) for c in df.columns
        },
        "invalid_email_count": int(sum(not patron.match(e.strip()) for e in correos)),
        "invalid_unit_count": int(sum(unidad_invalida(u) for u in unidades)),
        "country_values": sorted(df["country"].unique().tolist()) if "country" in df else [],
    }

    salida = base / "submission"
    salida.mkdir(exist_ok=True)
    (salida / "data_quality_report.json").write_text(
        json.dumps(reporte, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return reporte

