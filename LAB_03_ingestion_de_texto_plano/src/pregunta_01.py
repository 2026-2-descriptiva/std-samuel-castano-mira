def pregunta_01():
    """
    El archivo `data/clusters_report.txt` es un reporte de clústeres de
    palabras clave pensado para ser leído por una persona, no por un programa:
    los encabezados ocupan varias líneas, las columnas están alineadas con
    espacios y la lista de palabras clave de un clúster continúa en las líneas
    siguientes.

    Su tarea es convertir ese reporte en un DataFrame de Pandas con una fila
    por clúster y las columnas:

    - `cluster`: número del clúster, como entero.
    - `cantidad_de_palabras_clave`: como entero.
    - `porcentaje_de_palabras_clave`: como número decimal; por ejemplo, el
      texto `15,9 %` debe quedar como `15.9`.
    - `principales_palabras_clave`: todas las palabras clave del clúster en un
      solo texto, separadas por una coma y un único espacio.

    Retorne el DataFrame.

    Ejemplo del formato de la respuesta (se omite la última columna):

           cluster  cantidad_de_palabras_clave  porcentaje_de_palabras_clave
        0        1                         105                          15.9
        1        2                         102                          15.4
        ...
    """

    import re
    from pathlib import Path

    import pandas as pd

    ruta = Path(__file__).resolve().parents[1] / "data" / "clusters_report.txt"
    lineas = ruta.read_text(encoding="utf-8").splitlines()

    filas = []
    for linea in lineas:
        # Fila nueva: inicia con el numero del cluster.
        m = re.match(r"\s*(\d+)\s+(\d+)\s+(\d+,\d+)\s*%\s+(.*)", linea)
        if m:
            filas.append([int(m[1]), int(m[2]), float(m[3].replace(",", ".")), m[4]])
        elif filas and linea.strip() and not linea.startswith(("-", "Cluster")):
            # Continuacion de las palabras clave del cluster anterior.
            filas[-1][3] += " " + linea
    for fila in filas:
        texto = " ".join(fila[3].split()).rstrip(".")
        fila[3] = ", ".join(p.strip() for p in texto.split(","))

    return pd.DataFrame(
        filas,
        columns=[
            "cluster",
            "cantidad_de_palabras_clave",
            "porcentaje_de_palabras_clave",
            "principales_palabras_clave",
        ],
    )

