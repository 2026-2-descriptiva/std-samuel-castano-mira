from ._datos import leer_filas


def pregunta_04():
    """
    Cuente cuántos registros hay en cada mes, usando la fecha de la tercera
    columna (`date`). Represente el mes como un texto de dos dígitos y retorne
    una lista de tuplas `(mes, cantidad)` ordenada por el mes.

    Ejemplo del formato de la respuesta:

        [("01", 3), ("02", 4), ("03", 2), ...]
    """

    cuenta = {}
    for f in leer_filas():
        mes = f[2][5:7]
        cuenta[mes] = cuenta.get(mes, 0) + 1
    return sorted(cuenta.items())
