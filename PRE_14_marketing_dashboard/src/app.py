"""Dashboard de marketing (nicegui). Lee los CSV generados por main.py."""
from pathlib import Path

import pandas as pd
from nicegui import ui

SUB = Path(__file__).resolve().parent.parent / "submission"


def load(name):
    return pd.read_csv(SUB / name)


def build():
    kpis = load("kpis.csv").set_index("kpi")["value"]
    daily, src, camp = load("daily_summary.csv"), load("source_summary.csv"), load("campaign_summary.csv")

    ui.label("Dashboard de marketing").classes("text-2xl font-bold")
    with ui.row():
        for key, title, fmt in [("revenue", "Ingresos", "{:,.0f}"), ("ad_spend", "Gasto", "{:,.0f}"),
                                ("gross_profit", "Utilidad bruta", "{:,.0f}"), ("roas", "ROAS", "{:.2f}"),
                                ("ctr", "CTR", "{:.2%}"), ("cpc", "CPC", "{:.2f}")]:
            with ui.card():
                ui.label(title).classes("text-sm text-gray-500")
                ui.label(fmt.format(kpis[key])).classes("text-xl font-bold")

    monthly = daily.assign(mes=daily["date"].str[:7]).groupby("mes", as_index=False)[["revenue", "ad_spend"]].sum()
    ui.echart({
        "title": {"text": "Ingresos vs gasto por mes"}, "tooltip": {"trigger": "axis"},
        "legend": {"data": ["Ingresos", "Gasto"], "right": 0},
        "xAxis": {"type": "category", "data": monthly["mes"].tolist()}, "yAxis": {"type": "value"},
        "series": [{"name": "Ingresos", "type": "line", "data": monthly["revenue"].round(0).tolist()},
                   {"name": "Gasto", "type": "line", "data": monthly["ad_spend"].round(0).tolist()}],
    }).classes("w-full h-80")

    ui.label("Resumen por fuente").classes("text-lg font-bold")
    ui.table(columns=[{"name": c, "label": c, "field": c} for c in src.columns],
             rows=src.round(2).to_dict("records"))
    ui.label("Top 10 campanas por utilidad bruta").classes("text-lg font-bold")
    ui.table(columns=[{"name": c, "label": c, "field": c} for c in camp.columns],
             rows=camp.head(10).round(2).to_dict("records"))


@ui.page("/")
def index():
    build()


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title="Marketing", reload=False)
