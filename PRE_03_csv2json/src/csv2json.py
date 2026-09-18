"""
Conversion de archivos CSV a formato JSON.

El archivo de salida se escribe en la carpeta `temp` del mismo proyecto,
conservando el nombre del archivo de entrada pero con extension `.json`.
Cada fila del CSV se convierte en un objeto cuyas llaves son los nombres
de las columnas; todos los valores quedan como cadenas de texto.
"""

import csv
import json
import os

PROJECT_FOLDER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_FOLDER = os.path.join(PROJECT_FOLDER, "temp")


def load_csv(csv_file):
    """Lee el CSV y retorna una lista de diccionarios (una por fila)."""

    with open(csv_file, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save_json(data, json_file):
    """Escribe la lista de diccionarios como un archivo JSON."""

    os.makedirs(os.path.dirname(json_file), exist_ok=True)
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def convert_csv_2_json(csv_file, output_folder=OUTPUT_FOLDER):
    """Convierte `csv_file` a JSON y retorna la ruta del archivo generado."""

    name = os.path.splitext(os.path.basename(csv_file))[0]
    json_file = os.path.join(output_folder, f"{name}.json")
    save_json(load_csv(csv_file), json_file)
    return json_file


if __name__ == "__main__":
    print(convert_csv_2_json(os.path.join(PROJECT_FOLDER, "data", "drivers.csv")))
