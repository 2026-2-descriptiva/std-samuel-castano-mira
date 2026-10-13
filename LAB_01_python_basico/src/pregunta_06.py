from ._datos import leer_filas, pares


def pregunta_06():
    """
    La quinta columna (`metrics`) contiene pares `clave:valor` separados por
    comas. Para cada clave, encuentre el valor mínimo y el valor máximo que
    aparecen en todo el archivo. Retorne una lista de tuplas
    `(clave, mínimo, máximo)` ordenada alfabéticamente por la clave.

    Observe que el orden es mínimo y luego máximo, al contrario de la
    pregunta 5.

    Ejemplo del formato de la respuesta:

        [("aaa", 1, 9), ("bbb", 1, 9), ...]
    """

    valores = {}
    for f in leer_filas():
        for clave, valor in pares(f[4]):
            valores.setdefault(clave, []).append(valor)
    return [(k, min(v), max(v)) for k, v in sorted(valores.items())]
