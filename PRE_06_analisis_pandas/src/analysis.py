"""
Analisis de horas y millas por conductor usando pandas.

Cruza `drivers.csv` (datos del conductor) con `timesheet.csv` (registro
semanal) y deja en `submission` dos entregables:

- `summary.csv`: una fila por conductor con el total y el promedio de horas
  y millas registradas en el ano.
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


def load_data(drivers_file=DRIVERS_FILE, timesheet_file=TIMESHEET_FILE):
    """Lee los dos archivos de entrada."""

    return pd.read_csv(drivers_file), pd.read_csv(timesheet_file)


def build_summary(drivers, timesheet):
    """
    Une conductores con su registro semanal y agrega por conductor.

    Se usa un left join desde `drivers` para que un conductor sin registros
    aparezca en el resumen con ceros en vez de desaparecer del reporte.
    """

    aggregated = timesheet.groupby("driverId").agg(
        weeks=("week", "count"),
        total_hours=("hours-logged", "sum"),
        total_miles=("miles-logged", "sum"),
        mean_hours=("hours-logged", "mean"),
        mean_miles=("miles-logged", "mean"),
    )

    summary = drivers.merge(aggregated, on="driverId", how="left")
    counts = ["weeks", "total_hours", "total_miles"]
    summary[counts] = summary[counts].fillna(0).astype(int)
    summary[["mean_hours", "mean_miles"]] = summary[["mean_hours", "mean_miles"]].round(1)

    # Millas por hora: mide el rendimiento sin castigar a quien trabajo menos.
    summary["miles_per_hour"] = (
        (summary["total_miles"] / summary["total_hours"]).round(2).fillna(0)
    )

    # El resumen no publica ssn ni location: son identificadores directos y el
    # reporte es agregado, no los necesita.
    columns = [
        "driverId", "name", "certified", "wage-plan",
        "weeks", "total_hours", "total_miles",
        "mean_hours", "mean_miles", "miles_per_hour",
    ]
    summary = summary[columns]

    return summary.sort_values("total_miles", ascending=False).reset_index(drop=True)


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

    drivers, timesheet = load_data()
    summary = build_summary(drivers, timesheet)

    os.makedirs(SUBMISSION_FOLDER, exist_ok=True)
    summary.to_csv(SUMMARY_FILE, index=False)
    plot_top10(summary)
    return summary


if __name__ == "__main__":
    print(main().head(10).to_string())
