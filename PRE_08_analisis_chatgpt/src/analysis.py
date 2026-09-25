"""
Analisis de horas y millas por conductor asistido por un modelo de lenguaje.

El ejercicio consiste en resolver el analisis apoyandose en ChatGPT. El codigo
que quedo es el resultado de esa conversacion, ya revisado y corregido a mano:
los prompts usados y que hubo que ajustar de cada respuesta estan documentados
en `notebooks/notebook.ipynb`.

El resultado se valida contra las otras dos versiones del mismo analisis
(PRE_06 con pandas y PRE_07 con SQL), que dan cifras identicas.

Entregables en `submission`:
- `summary.csv`: una fila por conductor con totales y promedios del ano.
- `top10_drivers.png`: los diez conductores con mas millas recorridas.
"""

import os

import matplotlib

# Backend sin ventana: el grafico se guarda a archivo, nunca se muestra.
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

PROJECT_FOLDER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FOLDER = os.path.join(PROJECT_FOLDER, "data")
SUBMISSION_FOLDER = os.path.join(PROJECT_FOLDER, "submission")

DRIVERS_FILE = os.path.join(DATA_FOLDER, "drivers.csv")
TIMESHEET_FILE = os.path.join(DATA_FOLDER, "timesheet.csv")
SUMMARY_FILE = os.path.join(SUBMISSION_FOLDER, "summary.csv")
TOP10_FILE = os.path.join(SUBMISSION_FOLDER, "top10_drivers.png")


def build_summary(drivers, timesheet):
    """Agrega el registro semanal por conductor y lo cruza con sus datos."""

    aggregated = timesheet.groupby("driverId").agg(
        weeks=("week", "count"),
        total_hours=("hours-logged", "sum"),
        total_miles=("miles-logged", "sum"),
        mean_hours=("hours-logged", "mean"),
        mean_miles=("miles-logged", "mean"),
    )

    # Left join desde drivers: un conductor sin registros no debe desaparecer.
    summary = drivers.merge(aggregated, on="driverId", how="left")
    counts = ["weeks", "total_hours", "total_miles"]
    summary[counts] = summary[counts].fillna(0).astype(int)
    summary[["mean_hours", "mean_miles"]] = summary[["mean_hours", "mean_miles"]].round(1)
    summary["miles_per_hour"] = (
        (summary["total_miles"] / summary["total_hours"]).round(2).fillna(0)
    )

    # ssn y location son identificadores directos y el reporte es agregado.
    columns = [
        "driverId", "name", "certified", "wage-plan",
        "weeks", "total_hours", "total_miles",
        "mean_hours", "mean_miles", "miles_per_hour",
    ]
    return summary[columns].sort_values("total_miles", ascending=False).reset_index(drop=True)


def describe_findings(summary):
    """Hallazgos del analisis, para dejarlos escritos en el notebook."""

    by_plan = summary.groupby("wage-plan")["miles_per_hour"].mean().round(2)
    by_certified = summary.groupby("certified")["total_miles"].mean().round(0)
    leader = summary.iloc[0]
    median_miles = summary["total_miles"].median()

    return {
        "conductores": len(summary),
        "lider": f"{leader['name']} ({leader['total_miles']:,} millas)",
        "ventaja_lider_sobre_mediana": f"{leader['total_miles'] / median_miles:.2f}x",
        "millas_por_hora_segun_plan": by_plan.to_dict(),
        "millas_promedio_segun_certificacion": by_certified.to_dict(),
    }


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

    drivers = pd.read_csv(DRIVERS_FILE)
    timesheet = pd.read_csv(TIMESHEET_FILE)
    summary = build_summary(drivers, timesheet)

    os.makedirs(SUBMISSION_FOLDER, exist_ok=True)
    summary.to_csv(SUMMARY_FILE, index=False)
    plot_top10(summary)
    return summary


if __name__ == "__main__":
    summary = main()
    print(summary.head(10).to_string())
    print()
    for key, value in describe_findings(summary).items():
        print(f"{key}: {value}")
