"""
Analisis de horas y millas por conductor usando SQLite.

Mismo reporte que la version en pandas, pero la carga y la agregacion se hacen
con SQL sobre una base SQLite construida a partir de los CSV. pandas se usa
solo para llevar los datos a la base, recibir el resultado de la consulta y
dibujar el grafico.

Entregables en `submission`:
- `summary.csv`: una fila por conductor con totales y promedios del ano.
- `top10_drivers.png`: los diez conductores con mas millas recorridas.
"""

import os
import sqlite3

import matplotlib

# Backend sin ventana: el grafico se guarda a archivo, nunca se muestra.
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

PROJECT_FOLDER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FOLDER = os.path.join(PROJECT_FOLDER, "data")
SUBMISSION_FOLDER = os.path.join(PROJECT_FOLDER, "submission")
TEMP_FOLDER = os.path.join(PROJECT_FOLDER, "temp")

DRIVERS_FILE = os.path.join(DATA_FOLDER, "drivers.csv")
TIMESHEET_FILE = os.path.join(DATA_FOLDER, "timesheet.csv")
DATABASE_FILE = os.path.join(TEMP_FOLDER, "drivers.sqlite")
SUMMARY_FILE = os.path.join(SUBMISSION_FOLDER, "summary.csv")
TOP10_FILE = os.path.join(SUBMISSION_FOLDER, "top10_drivers.png")

# Un LEFT JOIN desde drivers para que un conductor sin registros siga
# apareciendo en el reporte (con ceros) en lugar de desaparecer.
SUMMARY_QUERY = """
    SELECT
        d.driverId                                   AS driverId,
        d.name                                       AS name,
        d.certified                                  AS certified,
        d."wage-plan"                                AS "wage-plan",
        COUNT(t.week)                                AS weeks,
        COALESCE(SUM(t."hours-logged"), 0)           AS total_hours,
        COALESCE(SUM(t."miles-logged"), 0)           AS total_miles,
        ROUND(AVG(t."hours-logged"), 1)              AS mean_hours,
        ROUND(AVG(t."miles-logged"), 1)              AS mean_miles,
        ROUND(
            COALESCE(SUM(t."miles-logged"), 0) * 1.0
            / NULLIF(SUM(t."hours-logged"), 0), 2
        )                                            AS miles_per_hour
    FROM drivers AS d
    LEFT JOIN timesheet AS t
        ON d.driverId = t.driverId
    GROUP BY d.driverId, d.name, d.certified, d."wage-plan"
    ORDER BY total_miles DESC
"""


def create_database(database_file=DATABASE_FILE):
    """Carga los dos CSV en una base SQLite y retorna la conexion abierta."""

    os.makedirs(os.path.dirname(database_file), exist_ok=True)
    if os.path.exists(database_file):
        os.remove(database_file)

    connection = sqlite3.connect(database_file)
    pd.read_csv(DRIVERS_FILE).to_sql("drivers", connection, index=False)
    pd.read_csv(TIMESHEET_FILE).to_sql("timesheet", connection, index=False)
    return connection


def build_summary(connection):
    """Ejecuta la consulta de agregacion y retorna el resultado."""

    return pd.read_sql_query(SUMMARY_QUERY, connection)


def plot_top10(summary, output_file=TOP10_FILE, n=10):
    """Guarda un grafico de barras con los `n` conductores de mas millas."""

    top = summary.nlargest(n, "total_miles").iloc[::-1]

    fig, ax = plt.subplots(figsize=(9, 5.5))
    bars = ax.barh(top["name"], top["total_miles"], color="#4C78A8")

    ax.set_xlabel("Millas recorridas en el año")
    ax.set_title(f"Top {n} conductores por millas recorridas")
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.set_xlim(0, top["total_miles"].max() * 1.12)

    # El valor va sobre la barra: se lee sin tener que seguir el eje.
    for bar, value in zip(bars, top["total_miles"]):
        ax.text(
            value * 1.01,
            bar.get_y() + bar.get_height() / 2,
            f"{value:,}",
            va="center",
            fontsize=9,
        )

    fig.tight_layout()
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    fig.savefig(output_file, dpi=150)
    plt.close(fig)
    return output_file


def main():
    """Genera los dos entregables y retorna el resumen."""

    connection = create_database()
    try:
        summary = build_summary(connection)
    finally:
        connection.close()

    os.makedirs(SUBMISSION_FOLDER, exist_ok=True)
    summary.to_csv(SUMMARY_FILE, index=False)
    plot_top10(summary)
    return summary


if __name__ == "__main__":
    print(main().head(10).to_string())
