from pathlib import Path

import pandas as pd

ACTIVITY_DIR = Path(__file__).resolve().parents[1]
BANDS = ["0%", "1%-5%", "6%-10%", "más de 10%"]


def _band(discount):
    """Rango de descuento según las reglas del enunciado."""
    if discount <= 0:
        return BANDS[0]
    if discount <= 0.05:
        return BANDS[1]
    if discount <= 0.10:
        return BANDS[2]
    return BANDS[3]


def _metrics(group):
    """Indicadores de rentabilidad de un grupo de líneas."""
    loss = group["Profit"] < 0
    sales = group["Sales"].sum()
    profit = group["Profit"].sum()
    return pd.Series(
        {
            "lines": len(group),
            "sales": sales,
            "profit": profit,
            "profit_margin": profit / sales,
            "loss_lines": int(loss.sum()),
            "loss_line_rate": loss.mean(),
            "lost_profit": -group.loc[loss, "Profit"].sum(),
        }
    )


def pregunta_01() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Una cadena de suministros de oficina vende mucho, pero la gerencia
    sospecha que parte de esas ventas no deja utilidad. El archivo
    `data/superstore_orders.csv.gz` tiene una fila por línea de pedido, con
    el número de pedido (`Order ID`), las ventas (`Sales`), la utilidad
    (`Profit`), el descuento aplicado (`Discount`, como proporción), el
    segmento del cliente (`Customer Segment`) y la categoría del producto
    (`Product Category`). Una utilidad negativa significa que la línea se
    vendió con pérdida.

    Use estas definiciones:

    - Margen (`profit_margin`): utilidad sobre ventas.
    - Línea con pérdida: una línea cuya utilidad es negativa.
    - `loss_line_rate`: la proporción de líneas con pérdida.
    - `lost_profit`: la suma de las pérdidas de las líneas con pérdida,
      escrita como número positivo.
    - Rango de descuento (`discount_band`): `0%` si no hubo descuento,
      `1%-5%` si fue mayor que 0 y hasta 5 %, `6%-10%` si fue mayor que 5 % y
      hasta 10 %, y `más de 10%` en otro caso.

    Genere tres archivos en `submission/`, sin el índice de Pandas y con las
    columnas en el orden indicado:

    1. `profitability_summary.csv`, con una sola fila: `lines` (cantidad de
       líneas), `orders` (pedidos distintos), `sales`, `profit`,
       `profit_margin`, `loss_lines` (cantidad de líneas con pérdida),
       `loss_line_rate` y `lost_profit`.

    2. `discount_summary.csv`, con una fila por rango de descuento, en el
       orden en que se definieron arriba: `discount_band`, `lines`, `sales`,
       `profit`, `profit_margin`, `loss_line_rate` y `lost_profit`.

    3. `priority_segments.csv`, con los cinco segmentos segmento–categoría
       que más utilidad pierden: `Customer Segment`, `Product Category`,
       `lines`, `sales`, `profit`, `profit_margin` y `lost_profit`. Considere
       solamente segmentos con al menos 100 líneas y ordénelos por
       `lost_profit` de mayor a menor.

    La función también debe retornar las tres tablas, en el mismo orden.

    Ejemplo del formato de `discount_summary.csv`:

        discount_band,lines,sales,profit,profit_margin,loss_line_rate,...
        0%,166,170539.05,29472.3789,0.1728,0.488,...
        ...
    """

    orders = pd.read_csv(
        ACTIVITY_DIR / "data" / "superstore_orders.csv.gz",
        sep=";",
        decimal=",",
        compression="gzip",
    )
    out_dir = ACTIVITY_DIR / "submission"
    out_dir.mkdir(exist_ok=True)

    total = _metrics(orders)
    summary = pd.DataFrame(
        [
            {
                "lines": int(total["lines"]),
                "orders": orders["Order ID"].nunique(),
                "sales": total["sales"],
                "profit": total["profit"],
                "profit_margin": total["profit_margin"],
                "loss_lines": int(total["loss_lines"]),
                "loss_line_rate": total["loss_line_rate"],
                "lost_profit": total["lost_profit"],
            }
        ]
    )

    bands = orders["Discount"].map(_band).rename("discount_band")
    discounts = (
        orders.groupby(bands)
        .apply(_metrics)
        .reindex(BANDS)
        .reset_index()
        .drop(columns="loss_lines")
    )
    discounts["lines"] = discounts["lines"].astype(int)

    keys = ["Customer Segment", "Product Category"]
    # Solo las columnas que usa _metrics: así las llaves del grupo no entran al apply.
    segments = orders.groupby(keys)[["Sales", "Profit"]].apply(_metrics).reset_index()
    segments = (
        segments[segments["lines"] >= 100]
        .sort_values("lost_profit", ascending=False)
        .head(5)
        .drop(columns=["loss_lines", "loss_line_rate"])
        .reset_index(drop=True)
    )
    segments["lines"] = segments["lines"].astype(int)

    tables = [summary, discounts, segments]
    names = ["profitability_summary", "discount_summary", "priority_segments"]
    for name, table in zip(names, tables):
        table.round(4).to_csv(out_dir / f"{name}.csv", index=False)

    return summary, discounts, segments
