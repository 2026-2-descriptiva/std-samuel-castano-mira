from ._datos import leer_filas


def pregunta_05():
    """
    Para cada letra de la primera columna (`letter`), encuentre el valor
    máximo y el valor mínimo de la segunda columna (`value`). Retorne una lista
    de tuplas `(letra, máximo, mínimo)` ordenada alfabéticamente por la letra.

    Ejemplo del formato de la respuesta:

        [("A", 9, 2), ("B", 9, 1), ...]
    """

    valores = {}
    for f in leer_filas():
        valores.setdefault(f[0], []).append(int(f[1]))
    return [(k, max(v), min(v)) for k, v in sorted(valores.items())]
