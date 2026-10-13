from ._datos import leer_filas


def pregunta_11():
    """
    La cuarta columna (`codes`) contiene letras minúsculas separadas por
    comas. Para cada una de esas letras, sume los valores de la segunda
    columna (`value`) de los registros en los que aparece. Retorne un
    diccionario `{letra: suma}` con las letras en orden alfabético.

    Ejemplo del formato de la respuesta:

        {"a": 122, "b": 49, "c": 91, ...}
    """

    suma = {}
    for f in leer_filas():
        for letra in f[3].split(","):
            suma[letra] = suma.get(letra, 0) + int(f[1])
    return dict(sorted(suma.items()))
