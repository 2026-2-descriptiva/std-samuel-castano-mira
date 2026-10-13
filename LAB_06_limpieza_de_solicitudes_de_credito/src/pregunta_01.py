def pregunta_01():
    """
    El archivo `data/solicitudes_de_credito.csv.gz` contiene las solicitudes de
    un programa de crédito, pero llegó sucio: tiene una columna de índice que
    no pertenece a los datos, registros duplicados, registros incompletos y
    valores que representan lo mismo escritos de formas distintas en los
    campos de texto, las fechas, el estrato y el monto.

    Su tarea es limpiarlo y guardar el resultado en
    `submission/solicitudes_de_credito.csv`, usando punto y coma (`;`) como
    separador y sin el índice de Pandas.

    El archivo limpio debe cumplir lo siguiente:

    - Contiene solamente las nueve columnas `sexo`, `tipo_de_emprendimiento`,
      `idea_negocio`, `barrio`, `estrato`, `comuna_ciudadano`,
      `fecha_de_beneficio`, `monto_del_credito` y `línea_credito`, en ese
      orden.
    - Los campos de texto están en minúsculas y sus palabras separadas por
      espacios.
    - `estrato` y `monto_del_credito` son números enteros, sin símbolos ni
      separadores de miles.
    - Todas las fechas de `fecha_de_beneficio` usan un mismo formato, por
      ejemplo `AAAA-MM-DD`.
    - No hay registros incompletos. La única excepción es
      `comuna_ciudadano`: sus valores faltantes son parte de los datos
      originales y deben conservarse.
    - No hay registros duplicados.

    Ejemplo del formato del archivo:

        sexo;tipo_de_emprendimiento;idea_negocio;barrio;estrato;...
        femenino;comercio;almacen de ropa en;los cerros el vergel;2;...
        ...
    """

    from pathlib import Path

    import pandas as pd

    base = Path(__file__).resolve().parents[1]
    df = pd.read_csv(base / "data" / "solicitudes_de_credito.csv.gz", sep=";")
    df = df.drop(columns="Unnamed: 0")

    # Texto: minúsculas, guiones a espacios y sin espacios en los extremos.
    for col in df.select_dtypes("object").columns.difference(["monto_del_credito", "fecha_de_beneficio"]):
        df[col] = df[col].str.lower().str.replace("-", " ", regex=False).str.strip()

    # Monto: quita "$", separadores de miles y decimales ".00".
    df["monto_del_credito"] = (
        df["monto_del_credito"]
        .astype(str)
        .str.replace(r"\.00$", "", regex=True)
        .str.replace(r"\D", "", regex=True)
        .astype(int)
    )

    # Fechas: tres formatos posibles.
    raw = df["fecha_de_beneficio"].astype(str)
    fechas = pd.to_datetime(raw, format="%d/%m/%Y", errors="coerce")
    for fmt in ("%Y/%m/%d", "%Y-%m-%d"):
        fechas = fechas.fillna(pd.to_datetime(raw, format=fmt, errors="coerce"))
    df["fecha_de_beneficio"] = fechas.dt.strftime("%Y-%m-%d")

    # Incompletos (salvo comuna) y duplicados.
    df = df.dropna(subset=[c for c in df.columns if c != "comuna_ciudadano"])
    df = df.drop_duplicates().reset_index(drop=True)
    df["comuna_ciudadano"] = df["comuna_ciudadano"].astype("Int64")

    out = base / "submission"
    out.mkdir(exist_ok=True)
    df.to_csv(out / "solicitudes_de_credito.csv", sep=";", index=False)
