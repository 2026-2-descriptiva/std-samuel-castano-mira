"""
Conteo de palabras usando el modelo MapReduce de forma secuencial.

Este archivo implementa el flujo completo (map, shuffle & sort, reduce)
sobre los archivos de texto de la carpeta `data`, escribiendo el resultado
en una carpeta de salida con el mismo formato que genera Hadoop:
un archivo `part-00000` con pares `palabra<TAB>conteo` y un marcador
`_SUCCESS`.
"""

import glob
import os.path
import re
import shutil

# La carpeta `data` vive junto a este modulo, asi que se resuelve de forma
# absoluta para que el codigo funcione sin importar desde donde se ejecute.
PROJECT_FOLDER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FOLDER = os.path.join(PROJECT_FOLDER, "data")
OUTPUT_FOLDER = os.path.join(PROJECT_FOLDER, "temp", "output_1")


def load_input(input_folder):
    """Lee los archivos de la carpeta y retorna una lista de (archivo, linea)."""

    sequence = []
    for file in glob.glob(f"{input_folder}/*"):
        with open(file, "r", encoding="utf-8") as f:
            for line in f:
                sequence.append((file, line))
    return sequence


def mapper(sequence):
    """Transforma cada linea en pares (palabra, 1)."""

    result = []
    for _, line in sequence:
        for word in re.sub(r"[^a-z]", " ", line.lower()).split():
            result.append((word, 1))
    return result


def shuffle_and_sort(sequence):
    """Ordena los pares por clave para agrupar las palabras iguales."""

    return sorted(sequence, key=lambda pair: pair[0])


def reducer(sequence):
    """Suma los valores de las claves iguales y consecutivas."""

    result = []
    for key, value in sequence:
        if result and result[-1][0] == key:
            result[-1] = (key, result[-1][1] + value)
        else:
            result.append((key, value))
    return result


def create_output_folder(output_folder):
    """Crea la carpeta de salida. Falla si la carpeta ya existe."""

    if os.path.exists(output_folder):
        raise FileExistsError(f"La carpeta '{output_folder}' ya existe.")
    os.makedirs(output_folder)


def save_output(output_folder, sequence):
    """Escribe los pares (clave, valor) en el archivo `part-00000`."""

    with open(f"{output_folder}/part-00000", "w", encoding="utf-8") as f:
        for key, value in sequence:
            f.write(f"{key}\t{value}\n")


def create_marker(output_folder):
    """Crea el archivo `_SUCCESS` que indica que el trabajo termino bien."""

    with open(f"{output_folder}/_SUCCESS", "w", encoding="utf-8") as f:
        f.write("")


def run(input_folder=DATA_FOLDER, output_folder=OUTPUT_FOLDER):
    """Ejecuta el job completo de conteo de palabras."""

    sequence = load_input(input_folder)
    sequence = mapper(sequence)
    sequence = shuffle_and_sort(sequence)
    sequence = reducer(sequence)
    create_output_folder(output_folder)
    save_output(output_folder, sequence)
    create_marker(output_folder)


if __name__ == "__main__":
    shutil.rmtree(OUTPUT_FOLDER, ignore_errors=True)
    run()
