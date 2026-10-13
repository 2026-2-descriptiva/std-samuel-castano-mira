from ._datos import leer_filas


def pregunta_02():
    """
    Cuente cuántos registros hay para cada letra de la primera columna
    (`letter`). Retorne una lista de tuplas `(letra, cantidad)` ordenada
    alfabéticamente por la letra.

    Ejemplo del formato de la respuesta:

        [("A", 8), ("B", 7), ("C", 5), ...]
    """

    cuenta = {}
    for f in leer_filas():
        cuenta[f[0]] = cuenta.get(f[0], 0) + 1
    return sorted(cuenta.items())
