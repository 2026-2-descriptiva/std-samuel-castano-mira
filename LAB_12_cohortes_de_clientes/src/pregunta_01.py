from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.ticker import PercentFormatter  # noqa: E402

ACTIVITY_DIR = Path(__file__).resolve().parents[1]


def build_cohort_analysis() -> pd.DataFrame:
    """
    Una tienda quiere saber si sus clientes vuelven a comprar después de su
    primera compra. Para responder, agrupe a los clientes en cohortes según
    el mes de su primera compra y mida, mes a mes, qué proporción de cada
    cohorte vuelve a comprar. Use `data/sales.csv.gz`, que tiene una fila por
    orden con su cliente (`CustomerID`) y su fecha (`OrderDate`).

    Use estas definiciones:

    - `cohort_month`: el mes de la primera compra del cliente, escrito como
      `AAAA-MM`.
    - `period_index`: los meses transcurridos desde `cohort_month`; es 0 en el
      mes de la primera compra, 1 en el mes siguiente, y así sucesivamente.
    - `active_customers`: la cantidad de clientes distintos de la cohorte que
      compraron en ese período.
    - `cohort_size`: la cantidad de clientes de la cohorte, es decir, sus
      clientes activos en el período 0.
    - `retention_rate`: `active_customers` sobre `cohort_size`.

    Genere dos archivos en `submission/`:

    1. `cohort_retention.csv`, sin el índice de Pandas, con las columnas
       `cohort_month`, `period_index`, `active_customers`, `cohort_size` y
       `retention_rate`, y una fila por cada combinación cohorte–período
       observada, ordenadas por cohorte y período.

    2. `cohort_retention_heatmap.png`, un mapa de calor de `retention_rate`
       con una fila por cohorte (eje vertical) y una columna por período
       (eje horizontal). Muestre los valores como porcentajes. Los períodos
       que todavía no se pueden observar para una cohorte no significan
       retención cero: déjelos vacíos en el mapa.

    La función también debe retornar la tabla de retención.

    Ejemplo del formato de `cohort_retention.csv`:

        cohort_month,period_index,active_customers,cohort_size,retention_rate
        2022-01,0,100,100,1.0
        2022-01,1,26,100,0.26
        ...
    """

    sales = pd.read_csv(
        ACTIVITY_DIR / "data" / "sales.csv.gz",
        usecols=["CustomerID", "OrderDate"],
        parse_dates=["OrderDate"],
    )
    out_dir = ACTIVITY_DIR / "submission"
    out_dir.mkdir(exist_ok=True)

    # Mes de cada orden y mes de la primera compra de cada cliente.
    sales["order_period"] = sales["OrderDate"].dt.to_period("M")
    sales["cohort_period"] = sales.groupby("CustomerID")["order_period"].transform(
        "min"
    )
    sales["period_index"] = (
        sales["order_period"].dt.year - sales["cohort_period"].dt.year
    ) * 12 + (sales["order_period"].dt.month - sales["cohort_period"].dt.month)
    sales["cohort_month"] = sales["cohort_period"].astype(str)

    retention = (
        sales.groupby(["cohort_month", "period_index"])["CustomerID"]
        .nunique()
        .rename("active_customers")
        .reset_index()
    )
    # Tamaño de la cohorte = clientes activos en el período 0.
    sizes = retention.loc[retention["period_index"] == 0].set_index("cohort_month")[
        "active_customers"
    ]
    retention["cohort_size"] = retention["cohort_month"].map(sizes)
    retention["retention_rate"] = (
        retention["active_customers"] / retention["cohort_size"]
    )
    retention = retention.sort_values(["cohort_month", "period_index"]).reset_index(
        drop=True
    )
    retention.to_csv(out_dir / "cohort_retention.csv", index=False)

    # Mapa de calor: los períodos no observados quedan como NaN (vacíos).
    matrix = retention.pivot(
        index="cohort_month", columns="period_index", values="retention_rate"
    )
    fig, ax = plt.subplots(figsize=(9, 6))
    image = ax.imshow(matrix.to_numpy(), cmap="Blues", vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(len(matrix.columns)))
    ax.set_xticklabels(matrix.columns)
    ax.set_yticks(range(len(matrix.index)))
    ax.set_yticklabels(matrix.index)
    ax.set_xlabel("Período (meses desde la primera compra)")
    ax.set_ylabel("Cohorte (mes de la primera compra)")
    ax.set_title("Retención de clientes por cohorte")
    for row, cohort in enumerate(matrix.index):
        for col, period in enumerate(matrix.columns):
            value = matrix.loc[cohort, period]
            if pd.notna(value):
                ax.text(
                    col,
                    row,
                    f"{value:.0%}",
                    ha="center",
                    va="center",
                    color="white" if value > 0.6 else "black",
                    fontsize=8,
                )
    fig.colorbar(image, ax=ax, format=PercentFormatter(1.0))
    fig.tight_layout()
    fig.savefig(out_dir / "cohort_retention_heatmap.png", dpi=150)
    plt.close(fig)

    return retention
