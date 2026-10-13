from ._datos import leer_filas, pares


def pregunta_12():
    """
    Para cada letra de la primera columna (`letter`), sume todos los valores
    numéricos de los pares `clave:valor` de la quinta columna (`metrics`).
    Retorne un diccionario `{letra: suma}` con las letras en orden alfabético.

    Ejemplo del formato de la respuesta:

        {"A": 177, "B": 187, "C": 114, ...}
    """

    suma = {}
    for f in leer_filas():
        suma[f[0]] = suma.get(f[0], 0) + sum(v for _, v in pares(f[4]))
    return dict(sorted(suma.items()))
