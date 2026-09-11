"""
Conteo de palabras emulando la ejecucion de un job de Hadoop.

La funcion `hadoop` recibe las funciones `mapper` y `reducer` como
parametros y ejecuta el flujo map / shuffle & sort / reduce sobre los
archivos de la carpeta de entrada, escribiendo el resultado en la carpeta
de salida (`part-00000` mas el marcador `_SUCCESS`).
"""

import glob
import os
import os.path
import re
import shutil

# La carpeta `data` vive junto a este modulo, asi que se resuelve de forma
# absoluta para que el codigo funcione sin importar desde donde se ejecute.
PROJECT_FOLDER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FOLDER = os.path.join(PROJECT_FOLDER, "data")

# Las carpetas de trabajo se dejan relativas porque el test las define asi y
# se las pasa a `hadoop`; ambos lados deben resolverlas contra el mismo cwd.
INPUT_FOLDER = "PRE_02_mapreduce/temp/input"
OUTPUT_FOLDER = "PRE_02_mapreduce/temp/output"


def delete_folder(folder):
    """Borra la carpeta y todo su contenido si existe."""

    shutil.rmtree(folder, ignore_errors=True)


def initialize_folder(folder):
    """Deja la carpeta creada y vacia."""

    delete_folder(folder)
    os.makedirs(folder)


def generate_file_copies(n, data_folder=DATA_FOLDER, input_folder=INPUT_FOLDER):
    """Copia `n` veces cada archivo de `data_folder` dentro de `input_folder`."""

    for file in glob.glob(f"{data_folder}/*"):
        stem, extension = os.path.splitext(os.path.basename(file))
        for i in range(1, n + 1):
            shutil.copy(file, f"{input_folder}/{stem}_{i}{extension}")


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


def hadoop(input_folder, output_folder, mapper_fn, reducer_fn):
    """Emula la ejecucion de un job de Hadoop con el mapper y reducer dados."""

    sequence = load_input(input_folder)
    sequence = mapper_fn(sequence)
    sequence = shuffle_and_sort(sequence)
    sequence = reducer_fn(sequence)
    create_output_folder(output_folder)
    save_output(output_folder, sequence)
    create_marker(output_folder)


if __name__ == "__main__":
    initialize_folder(INPUT_FOLDER)
    delete_folder(OUTPUT_FOLDER)
    generate_file_copies(10)
    hadoop(INPUT_FOLDER, OUTPUT_FOLDER, mapper, reducer)
