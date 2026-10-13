from ._datos import leer_filas, pares


def pregunta_09():
    """
    Cuente cuántas veces aparece cada clave en la quinta columna (`metrics`)
    de todo el archivo. Retorne un diccionario `{clave: cantidad}` con las
    claves en orden alfabético.

    Ejemplo del formato de la respuesta:

        {"aaa": 13, "bbb": 16, "ccc": 23, ...}
    """

    cuenta = {}
    for f in leer_filas():
        for clave, _ in pares(f[4]):
            cuenta[clave] = cuenta.get(clave, 0) + 1
    return dict(sorted(cuenta.items()))
