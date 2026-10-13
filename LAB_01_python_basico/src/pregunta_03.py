from ._datos import leer_filas


def pregunta_03():
    """
    Sume los valores de la segunda columna (`value`) para cada letra de la
    primera columna (`letter`). Retorne una lista de tuplas `(letra, suma)`
    ordenada alfabéticamente por la letra.

    Ejemplo del formato de la respuesta:

        [("A", 53), ("B", 36), ("C", 27), ...]
    """

    suma = {}
    for f in leer_filas():
        suma[f[0]] = suma.get(f[0], 0) + int(f[1])
    return sorted(suma.items())
