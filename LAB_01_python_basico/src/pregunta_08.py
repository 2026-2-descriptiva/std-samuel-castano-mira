from ._datos import leer_filas


def pregunta_08():
    """
    Repita la pregunta 7, pero ahora cada lista de letras debe contener cada
    letra una sola vez y estar ordenada alfabéticamente. Retorne una lista de
    tuplas `(valor, letras)` ordenada por el valor.

    Ejemplo del formato de la respuesta:

        [(0, ["C"]), (1, ["B", "E"]), (2, ["A", "E"]), ...]
    """

    grupos = {}
    for f in leer_filas():
        grupos.setdefault(int(f[1]), set()).add(f[0])
    return [(k, sorted(v)) for k, v in sorted(grupos.items())]
